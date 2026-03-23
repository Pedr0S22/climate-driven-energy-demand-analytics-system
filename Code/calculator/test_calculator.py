import sys
import os
import pytest

# --- PATH CONFIGURATION ---
# This forces Python to add your 'Code' and 'calculator' directories to its search path
# so it can find 'our_add.our_add', etc., without ModuleNotFoundErrors.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
print(current_dir)
print(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
# --------------------------

from calculator import main

def test_addition_integration(monkeypatch, capsys):
    # 1. monkeypatch simulates typing this into the command line
    monkeypatch.setattr("sys.argv", ['calculator.py', '+', '10', '5'])
    
    # 2. Run the script
    main()
    
    # 3. capsys grabs everything the script printed to the terminal
    output = capsys.readouterr().out
    
    # 4. Standard Python asserts replace self.assertIn
    assert "operation: +" in output
    assert "first argument: 10" in output
    assert "second argument: 5" in output
    assert "10 + 5 = 15" in output  # Assumes our_add(10, 5) == 15

def test_subtraction_integration(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ['calculator.py', '-', '10', '5'])
    main()
    output = capsys.readouterr().out
    
    assert "operation: -" in output
    assert "10 - 5 = 5" in output

def test_multiplication_integration(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ['calculator.py', '*', '10', '5'])
    main()
    output = capsys.readouterr().out
    
    assert "operation: *" in output
    assert "10 * 5 = 50" in output

def test_division_integration(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ['calculator.py', '/', '10', '5'])
    main()
    output = capsys.readouterr().out
    
    assert "operation: /" in output
    assert "10 / 5 = 2" in output or "10 / 5 = 2.0" in output

def test_modulo_integration(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ['calculator.py', '%', '10', '5'])
    main()
    output = capsys.readouterr().out
    
    assert "operation: %" in output
    assert "10 and 5 with mod operation =" in output

def test_invalid_operation(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ['calculator.py', '^', '10', '5'])
    main()
    output = capsys.readouterr().out
    
    assert "Invalid operation: ^" in output

def test_missing_arguments(monkeypatch, capsys):
    # Only 2 arguments provided
    monkeypatch.setattr("sys.argv", ['calculator.py', '+'])
    main()
    output = capsys.readouterr().out
    
    assert "Number of arguments must be exactly three" in output

def test_too_many_arguments(monkeypatch, capsys):
    # 5 arguments provided
    monkeypatch.setattr("sys.argv", ['calculator.py', '+', '10', '5', '8'])
    main()
    output = capsys.readouterr().out
    
    assert "Number of arguments must be exactly three" in output