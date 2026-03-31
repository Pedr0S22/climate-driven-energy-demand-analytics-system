import pandas as pd
import os
import numpy as np

# =======================================
# DADOS ENERGY
# =======================================


def fill_nan_energy(df):
    df["Load_MW"] = pd.to_numeric(df["Load_MW"], errors="coerce")
    if df["Load_MW"].isna().sum() == 0:
        return df

    # quando for NaN na 1 linha
    for idx in df[df["Load_MW"].isna()].index:
        if idx == 0:  # Primeira linha
            if idx + 1 < len(df) and pd.notna(df.loc[idx + 1, "Load_MW"]):
                df.loc[idx, "Load_MW"] = df.loc[idx + 1, "Load_MW"]
                continue

    # Identificar cada NaN e quantos existem na mesma hora
    for idx in df[df["Load_MW"].isna()].index:
        hora_atual = df.loc[idx, "Unnamed: 0"].floor("h")
        mask_mesma_hora = df["Unnamed: 0"].dt.floor("h") == hora_atual
        num_nan_hora = df.loc[mask_mesma_hora, "Load_MW"].isna().sum()

        if num_nan_hora == 1:
            # Apenas 1 NaN na hora - interpolação (apenas neste ponto)
            df.loc[idx, "Load_MW"] = df["Load_MW"].interpolate(method="linear").loc[idx]
        else:
            # Mais que 1 NaN na hora - média das últimas 6 observações válidas
            dados_anteriores = df.loc[: idx - 1, "Load_MW"].dropna().tail(6)
            if len(dados_anteriores) > 0:
                df.loc[idx, "Load_MW"] = dados_anteriores.mean()

    return df


def aggregate_hour(df):
    time_col = "Unnamed: 0"
    value_col = "Load_MW"

    df = df.sort_values(time_col).reset_index(drop=True)
    df[time_col] = pd.to_datetime(df[time_col], utc=True)

    idx_15_start = df.attrs.get("idx_15_start", None)

    # --- CASO 1: 15 min contínuo (sem idx_15_start guardado) ---
    if idx_15_start is None:
        # assume que TUDO é 15 min
        i = 0
        indices_para_apagar = []

        while i < len(df):
            hora_atual = df.loc[i, time_col].floor("h")
            valores_hora = []
            indices_hora = []

            while i < len(df) and df.loc[i, time_col].floor("h") == hora_atual:
                valores_hora.append(df.loc[i, value_col])
                indices_hora.append(i)
                i += 1

            if valores_hora:
                valor_max = max(valores_hora)
                df.loc[indices_hora[0], value_col] = valor_max
                for idx in indices_hora[1:]:
                    indices_para_apagar.append(idx)

        df = df.drop(indices_para_apagar).reset_index(drop=True)
        print(f"  Shape antes: {len(df) + len(indices_para_apagar)} (15min)")
        print(f"  Shape depois: {len(df)} (1h com máximo)")

    # --- CASO 2: mistura 1h + 15 min (com idx_15_start guardado) ---
    else:
        df_horario = df.iloc[:idx_15_start].copy().reset_index(drop=True)
        df_15min = df.iloc[idx_15_start:].copy().reset_index(drop=True)

        i = 0
        indices_para_apagar = []

        while i < len(df_15min):
            hora_atual = df_15min.loc[i, time_col].floor("h")
            valores_hora = []
            indices_hora = []

            while (
                i < len(df_15min) and df_15min.loc[i, time_col].floor("h") == hora_atual
            ):
                valores_hora.append(df_15min.loc[i, value_col])
                indices_hora.append(i)
                i += 1

            if valores_hora:
                valor_max = max(valores_hora)
                df_15min.loc[indices_hora[0], value_col] = valor_max
                for idx in indices_hora[1:]:
                    indices_para_apagar.append(idx)

        df_15min = df_15min.drop(indices_para_apagar).reset_index(drop=True)

        df_final = pd.concat([df_horario, df_15min], ignore_index=True)
        df_final = df_final.sort_values(time_col).reset_index(drop=True)

        print("  Mistura 1h + 15 min: 15 min → 1h agregado.")
        print(f"  Shape final: {len(df_final)} (1h com máximo)")

        return df_final

    return df


def energy(pasta_energy, pasta_saida=None):
    for nomefich in sorted(os.listdir(pasta_energy)):
        if nomefich.endswith(".csv"):
            caminho = os.path.join(pasta_energy, nomefich)
            df = pd.read_csv(caminho)
            print(f"\n=== {nomefich} ===")
            print("Colunas:", list(df.columns))
            print(df.dtypes)
            print("Primeiras linhas:")
            print(df.head())
            print("Shape:", df.shape)
            n_nan_total = df["Load_MW"].isna().sum()
            print(f"   Total: {n_nan_total} missing")  # há 0 valores em falta

            # mudar o timestamp para formato UTC
            # em 2020 e 2021 o horário está de 1h em 1h; 2022 tem de 1h em 1h e
            # de 15min em 15min; o resto é de 15min em 15min
            print("###########")
            df["Unnamed: 0"] = pd.to_datetime(df["Unnamed: 0"], utc=True)
            # mostra 5 linhas com a coluna já em UTC (mesmo nome!) ===
            print("##### COLUNA 'Unnamed: 0' EM UTC (5 primeiras linhas) #####")
            print(df["Unnamed: 0"].head(5))
            print("DataFrame completo com coluna em UTC (5 primeiras linhas):")
            print(df.head(5))

            df_e = time_alignment_energy(df)

            if pasta_saida:
                os.makedirs(pasta_saida, exist_ok=True)
                caminho_saida = os.path.join(pasta_saida, nomefich)
                df_e.to_csv(caminho_saida, index=False)
                print(f" Ficheiro corrigido guardado em: {caminho_saida}")


def time_alignment_energy(df):
    time_col = "Unnamed: 0"
    df = df.copy()
    df = df.sort_values(time_col).reset_index(drop=True)

    # Diferenças entre linhas consecutivas
    ts = df["Unnamed: 0"]
    diffs = ts.diff().dropna().unique()

    print("\nFREQUÊNCIA TEMPORAL:")
    print("Diferenças encontradas no dataset:")
    for d in diffs:
        print(d)

    if len(diffs) == 1:
        d = diffs[0]
        if d == pd.Timedelta(hours=1):
            return df
        elif d == pd.Timedelta(minutes=15):
            return g15_energy(df)
        else:
            return ajust15_energy(df)

    else:
        # Tem mais do que um intervalo
        unique_diffs = set(diffs)

        if {pd.Timedelta(hours=1), pd.Timedelta(minutes=15)}.issubset(unique_diffs):
            return g115g1(df)
        else:
            return g15_energy(df)


def g15_energy(df):
    time_col = "Unnamed: 0"
    df = df.sort_values(time_col).reset_index(drop=True)
    novas_linhas = []

    for i in range(len(df) - 1):
        linha_atual = df.iloc[i].to_dict()
        tempo_atual = df.loc[i, time_col]
        prox_tempo = df.loc[i + 1, time_col]

        novas_linhas.append(linha_atual)
        diff = prox_tempo - tempo_atual

        if diff > pd.Timedelta(minutes=15):
            # Todos os intervalos de 15 min entre tempo_atual e prox_tempo
            tempos_em_falta = pd.date_range(
                start=tempo_atual + pd.Timedelta(minutes=15),
                end=prox_tempo - pd.Timedelta(minutes=15),
                freq="15min",
                name=time_col,
            )
            for t in tempos_em_falta:
                nova_linha = {col: pd.NA for col in df.columns}
                nova_linha[time_col] = t
                novas_linhas.append(nova_linha)
    # Adicionar última linha
    novas_linhas.append(df.iloc[-1].to_dict())

    # Construir novo df
    df_novo = pd.DataFrame(novas_linhas)
    df_novo = df_novo.sort_values(time_col).reset_index(drop=True)
    df_novo_energy = fill_nan_energy(df_novo)
    df_fim = aggregate_hour(df_novo_energy)
    return df_fim


def ajust15_energy(df):
    df["Unnamed: 0"] = df["Unnamed: 0"].dt.round("15min")
    return g15_energy(df)


def g115g1(df):
    time_col = "Unnamed: 0"
    df = df.sort_values(time_col).reset_index(drop=True)

    # Calcular diferenças entre linhas consecutivas
    diffs = df[time_col].diff().dropna().values

    # Procurar onde a dif passa de 1h para 15 min
    idx_15_start = None
    for i in range(1, len(diffs)):
        prev_diff = diffs[i - 1]
        this_diff = diffs[i]
        if prev_diff >= pd.Timedelta(hours=1) and this_diff == pd.Timedelta(minutes=15):
            idx_15_start = i - 1  # 2 linhas acima da linha onde encontra a dif 15min
            break

    # Verificar se encontrou transição válida
    if idx_15_start is None:
        return df  # Se não encontrar transição, retorna df original

    # Acima (1h): até idx_15_start (inclusive)
    df_1H = df.iloc[: idx_15_start + 1].copy().reset_index(drop=True)

    # A partir da linha seguinte (15 min): chama g15_energy
    df_15 = df.iloc[idx_15_start + 1 :].copy().reset_index(drop=True)
    df_15 = g15_energy(df_15)
    df_15.attrs["idx_15_start"] = idx_15_start

    # Junta tudo
    df_final = pd.concat([df_1H, df_15], ignore_index=True)
    df_final = df_final.sort_values(time_col).reset_index(drop=True)
    df_final.attrs["idx_15_start"] = idx_15_start

    return df_final


# =======================================
# DADOS WEATHER
# =======================================


def weather(pasta_saida=None):
    datasets = [
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/era5_timeseries_2020-01-01_to_2025-12-31.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-2m-temperatureauafbxo0.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-pressure-precipitationtwpvvkbd.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-radiation-heathoyt7mym.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-skin-temperaturercarv5g8.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-soil-temperatureokgb55eq.csv",
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather/reanalysis-era5-land-timeseries-sfc-soil-waterp9pn16zx.csv",
    ]

    for arquivo in datasets:
        print(f"\n--- {arquivo} ---")
        print("##########")
        print("##########")
        df = pd.read_csv(arquivo)

        print("Colunas:", list(df.columns))
        print(df.info())
        print("Valores nulos por coluna:")
        print(df.isnull().sum())  # não há valores nulos em nenhum dataset
        print("Primeiras linhas:")
        print(df.head())
        print("Shape:", df.shape)

        df = convert_era5_units(df)
        print("\n=== DEPOIS DAS CONVERSÕES ===")
        print(df.head())
        print("Shape após conversões:", df.shape)

        df_aligned = time_alignment(df)
        df_clean = outliers_treatment(df_aligned)

        df_hourly = hourly_aggregation(df_clean)
        if pasta_saida:
            nome_saida = os.path.basename(arquivo)
            caminho_saida = os.path.join(pasta_saida, nome_saida)
            df_hourly.to_csv(caminho_saida, index=False)


def convert_era5_units(df):
    df = df.copy()

    # TEMPERATURAS: Kelvin → Celsius
    temp_vars = ["skt", "t2m", "d2m", "stl1"]
    for var in temp_vars:
        if var in df.columns:
            df[var] = df[var] - 273.15

    # RADIAÇÃO: J/m² → W/m²
    rad_vars = ["ssrd", "strd"]
    for var in rad_vars:
        if var in df.columns:
            df[var] = df[var] / 900

    # PRESSÃO: Pa → hPa
    if "sp" in df.columns:
        df["sp"] = df["sp"] / 100

    # PRECIPITAÇÃO: m → mm
    if "tp" in df.columns:
        df["tp"] = df["tp"] * 1000

    return df


def time_alignment(df):
    df["valid_time"] = pd.to_datetime(df["valid_time"], utc=True)

    # Diferença entre cada linha e a anterior
    df["diff"] = df["valid_time"].diff()
    print("\nFREQUÊNCIA TEMPORAL:")

    # Pega apenas as diferenças válidas e únicas
    diffs_unicos = df["diff"].dropna().unique()
    print("Diferenças encontradas no dataset:")
    for d in diffs_unicos:
        print(d)

    if len(diffs_unicos) == 1:
        if diffs_unicos[0] == pd.Timedelta(hours=1):
            return df
        elif diffs_unicos[0] == pd.Timedelta(minutes=15):
            df = g15min(df)
        else:
            df = ajust15(df)
    else:
        df = ajust15(df)

    return df


def g15min(df):
    df = df.sort_values("valid_time").reset_index(drop=True)
    novas_linhas = []

    for i in range(len(df) - 1):
        linha_atual = df.iloc[i].to_dict()
        prox_tempo = df.loc[i + 1, "valid_time"]
        tempo_atual = df.loc[i, "valid_time"]

        novas_linhas.append(linha_atual)
        diff = prox_tempo - tempo_atual
        if diff > pd.Timedelta(minutes=15):
            tempos_em_falta = pd.date_range(
                start=tempo_atual + pd.Timedelta(minutes=15),
                end=prox_tempo - pd.Timedelta(minutes=15),
                freq="15min",
            )
            for t in tempos_em_falta:
                nova_linha = {col: np.nan for col in df.columns}
                nova_linha["valid_time"] = t
                novas_linhas.append(nova_linha)

    novas_linhas.append(df.iloc[-1].to_dict())
    df_novo = pd.DataFrame(novas_linhas)
    df_novo = df_novo.sort_values("valid_time").reset_index(drop=True)

    return missingValuesFind(df_novo)


def ajust15(df):
    df["valid_time"] = df["valid_time"].dt.round("15min")
    return g15min(df)


def missingValuesFind(df):
    ignore_cols = ["valid_time", "latitude", "longitude"]
    vars_analisar = [col for col in df.columns if col not in ignore_cols]
    df = df.copy()
    df.set_index("valid_time", inplace=True)
    for var in vars_analisar:
        df[var] = missingImputation(df, var)
    return df.reset_index()


def missingImputation(df, var):
    hourly_groups = df.groupby(df.index.floor("1h"))
    resultado = []

    for hora, group in hourly_groups:
        serie = group[var]
        nan_count = serie.isna().sum()
        if nan_count == 0:
            resultado.append(serie)
        elif nan_count == 1:
            resultado.append(serie.interpolate(method="linear", limit_direction="both"))
        else:
            print(f"{var} | {hora}: ESTRATÉGIA ESPECÍFICA")
            if var in ["t2m", "skt", "stl1", "d2m", "strd"]:
                resultado.append(temp_termicRad_imputation(serie))
            elif var in ["u10", "v10"]:
                resultado.append(wind_imputation(serie))
            elif var == "ssrd":
                resultado.append(solar_imputation(serie))
            elif var == "tp":
                resultado.append(precip_imputation(serie))
            elif var == "sp":
                resultado.append(pressure_imputation(serie))
            elif var == "swvl1":
                resultado.append(soil_imputation(serie))
            else:
                resultado.append(serie.interpolate(method="linear"))

    return pd.concat(resultado)


# FUNÇÕES ESPECÍFICAS POR TIPO
def temp_termicRad_imputation(series):
    """Média 4 anteriores + 2 seguintes válidas"""
    return media_custom(series, n_prev=4, n_next=2)


def wind_imputation(series):
    """Média últimas 3"""
    return media_custom(series, n_prev=3, n_next=0)


def solar_imputation(series):
    s = series.copy()

    for idx in range(len(s)):
        hora = s.index[idx].hour
        if (hora >= 22 or hora <= 4) and pd.isna(s.iloc[idx]):
            s.iloc[idx] = 0
        elif pd.isna(s.iloc[idx]):
            s.iloc[idx] = media_custom(s, n_prev=4, n_next=2).iloc[idx]

    return s


def precip_imputation(series):
    s = series.astype(float).copy()
    zeros_vizinhos = s.rolling(3, center=True, min_periods=1).sum() == 0
    s[zeros_vizinhos] = 0
    s = media_custom(s, n_prev=3, n_next=0)
    return s


def pressure_imputation(series):
    """Média últimas 4"""
    return media_custom(series, n_prev=4, n_next=0)


def soil_imputation(series):
    """Média últimas 6"""
    return media_custom(series, n_prev=6, n_next=0)


def media_custom(series, n_prev, n_next):
    """Média N prev + N next válidas"""
    s = series.copy()
    result = s.copy()

    for i in range(len(s)):
        if pd.isna(s.iloc[i]):
            start = max(0, i - n_prev)
            end = min(len(s), i + n_next + 1)
            window_vals = s.iloc[start:end].dropna()
            if len(window_vals) > 0:
                result.iloc[i] = window_vals.mean()

    return result.ffill().bfill()


# outliers
def outliers_treatment(df):
    ignore_cols = ["valid_time", "latitude", "longitude"]
    vars_analisar = [col for col in df.columns if col not in ignore_cols]

    df = df.copy()
    df.set_index("valid_time", inplace=True)

    limites_fisicos = {
        # Temperature: -40°C a 55°C (solo até 65°C)
        "t2m": (-40, 55),
        "skt": (-40, 55),
        "d2m": (-40, 55),
        "stl1": (-40, 65),
        # Wind: 0-250 km/h- 69.4 m/s
        "u10": (0, 69.4),
        "v10": (0, 69.4),
        # Precipitation: 0-55 mm/15min
        "tp": (0, 55),
        # Solar: >=0 dia
        "ssrd": (0, float("inf")),
    }
    iqr_only = ["strd", "sp", "swvl1"]  # Só IQR
    for var in vars_analisar:
        # IQR para TODAS variáveis
        Q1 = df[var].quantile(0.25)
        Q3 = df[var].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Detecta outliers IQR
        outliers_candidatos = (df[var] < lower_bound) | (df[var] > upper_bound)
        n_candidatos = outliers_candidatos.sum()
        print(f"  IQR outliers: {n_candidatos}")

        # Verifica limites físicos
        if var in limites_fisicos:
            limite_min, limite_max = limites_fisicos[var]
            outliers_reais = outliers_candidatos & (
                (df[var] < limite_min) | (df[var] > limite_max)
            )
            n_outliers_reais = outliers_reais.sum()
            print(f"  Limites físicos: {n_outliers_reais}")

            # outliers fora dos limites físicos
            if n_outliers_reais > 0:
                df.loc[outliers_reais, var] = np.nan
                outliers_tratar = outliers_reais
                if var in ["t2m", "skt", "d2m", "stl1", "u10", "v10"]:
                    # média 4 prev + 2 next
                    df.loc[outliers_tratar, var] = media_custom(df[var], 4, 2)

                elif var in ["ssrd", "tp"]:
                    # média 2 mais próximas
                    df.loc[outliers_tratar, var] = media_nearest(df[var], n_nearest=2)

        elif var in iqr_only:
            if n_candidatos > 0:
                df.loc[outliers_candidatos, var] = np.nan
                if var == "strd":
                    # média 2 vizinhos mais próximos
                    df.loc[outliers_candidatos, var] = media_nearest(
                        df[var], n_nearest=2
                    )
                elif var == "sp":
                    # média 4 prev + 2 next
                    df.loc[outliers_candidatos, var] = media_custom(df[var], 4, 2)
                elif var == "swvl1":
                    # últimas 6
                    df.loc[outliers_candidatos, var] = media_custom(df[var], 6, 0)

        else:
            print("manter")

    return df.reset_index()


def media_nearest(series, n_nearest=2):
    s = series.copy()
    result = s.copy()

    for i in range(len(s)):
        validos_antes = []
        j = i - 1
        while len(validos_antes) < n_nearest and j >= 0:
            if pd.notna(s.iloc[j]) and np.isfinite(s.iloc[j]):
                validos_antes.append(s.iloc[j])
            j -= 1

        if len(validos_antes) == 2:
            result.iloc[i] = np.mean(validos_antes)

    return result.ffill().bfill()


def hourly_aggregation(df):
    df = df.copy()
    diffs = df["valid_time"].diff().dropna()
    if len(diffs.unique()) == 1 and diffs.iloc[0] == pd.Timedelta(minutes=15):
        i = 0
        indices_para_apagar = []
        while i < len(df):
            hora_atual = df.loc[i, "valid_time"].floor("h")
            indices_hora = []
            # mesma hora
            while i < len(df) and df.loc[i, "valid_time"].floor("h") == hora_atual:
                indices_hora.append(i)
                i += 1
            if len(indices_hora) > 1:
                primeiro_idx = indices_hora[0]
                # MÉDIA de TODAS colunas exceto valid_time, latitude, longitude
                cols_to_average = [
                    col
                    for col in df.columns
                    if col not in ["valid_time", "latitude", "longitude"]
                ]
                for col in cols_to_average:
                    df.loc[primeiro_idx, col] = df.loc[indices_hora, col].mean()
                # Apaga xx:15, xx:30, xx:45
                for idx in indices_hora[1:]:
                    indices_para_apagar.append(idx)
        df = df.drop(indices_para_apagar).reset_index(drop=True)

    else:
        print(" Já está de 1h em 1h")

    return df.sort_values("valid_time").reset_index(drop=True)


# =======================================
# JUNTAR DATASETS
# =======================================
def cleaning(pasta_energy_corrigido, pasta_weather_corrigido):
    pasta_saida = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
    os.makedirs(pasta_saida, exist_ok=True)

    # 1. energy
    dfs_energy = []
    for f in sorted(os.listdir(pasta_energy_corrigido)):
        if f.endswith(".csv"):
            caminho = os.path.join(pasta_energy_corrigido, f)
            df = pd.read_csv(caminho)
            df["datetime"] = pd.to_datetime(df["Unnamed: 0"], utc=True)
            df = df[["datetime", "Load_MW"]]
            dfs_energy.append(df)

    df_energy = pd.concat(dfs_energy, ignore_index=True)
    df_energy = (
        df_energy.drop_duplicates("datetime")
        .sort_values("datetime")
        .reset_index(drop=True)
    )
    print(f"Energy: {len(df_energy)} registos únicos")

    # 2. weather
    dfs_weather = []
    cols_excluir = ["latitude", "longitude", "diff"]

    for f in sorted(os.listdir(pasta_weather_corrigido)):
        if f.endswith(".csv"):
            caminho = os.path.join(pasta_weather_corrigido, f)
            df = pd.read_csv(caminho)
            df["datetime"] = pd.to_datetime(df["valid_time"], utc=True)

            # Remove colunas indesejadas e mantém só variáveis meteo
            cols_manter = [col for col in df.columns if col not in cols_excluir]
            df = df[cols_manter]
            dfs_weather.append(df)

    df_weather = pd.concat(dfs_weather, ignore_index=True)
    df_weather = df_weather.groupby("datetime").mean(numeric_only=True).reset_index()
    print(f" Weather: {len(df_weather)} registos únicos")

    # 3. juntar
    df_final = pd.merge(df_weather, df_energy, on="datetime", how="inner")

    # 4. verificar
    print(f"\n DATASET FINAL:")
    print(f"   Shape: {df_final.shape}")
    print(f"   Colunas: {list(df_final.columns)}")
    print(f"   Período: {df_final['datetime'].min()} → {df_final['datetime'].max()}")

    nulos = df_final.isnull().sum()
    if nulos.sum() > 0:
        print(f"\n Valores em falta:")
        print(nulos[nulos > 0])
    else:
        print("\n SEM valores em falta!")

    nome_final = "dados_finais_completos.csv"
    caminho_final = os.path.join(pasta_saida, nome_final)
    df_final.to_csv(caminho_final, index=False)

    return df_final


# =======================================
# MAIN
# =======================================


if __name__ == "__main__":
    caminho_energy = "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/energy"
    caminho_weather = "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/Weather"
    pasta_final = "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/processed"

    caminho_energy_corrigido = (
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/energy_corrigido"
    )
    energy(caminho_energy, pasta_saida=caminho_energy_corrigido)

    caminho_weather_corrigido = (
        "/Users/beatrizfernandes/Desktop/PIACD/dados_PIACD/weather_corrigido"
    )
    weather(pasta_saida=caminho_weather_corrigido)

    df_final = cleaning(
        pasta_energy_corrigido=caminho_energy_corrigido,
        pasta_weather_corrigido=caminho_weather_corrigido,
    )
