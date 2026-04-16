# How to Use Traefik for API Gateway & Rate Limiting for QA5

**Goal:** Set up Traefik as a reverse proxy to automatically discover our Docker containers, route traffic, and enforce rate limits to protect our API from extreme user load and ensure QA5 is met.

Traefik can and should be configured to intercept every incoming request and check the cryptographic validity of the JWT before the request ever touches your backend. If a bot, a hacker, or a user with an expired session tries to hit your API, Traefik instantly drops the request and returns a 401 Unauthorized. Your application server doesn't waste a single CPU cycle dealing with fake traffic.

### Step 1: Create the docker-compose.yml
Traefik configuration in Docker is entirely label-based. You do not need a separate configuration file; everything lives right here in the Compose file.

Create a docker-compose.yml file and paste the following:

```YAML
services:
  # --------------------------------------------------------
  # 1. THE GATEWAY (TRAEFIK)
  # --------------------------------------------------------
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true" # Enables the Traefik UI on port 8080 (Local dev only)
      - "--providers.docker=true" # Listens to the Docker daemon for new containers
      - "--providers.docker.exposedbydefault=false" # Only exposes containers with the 'enable=true' label
      - "--entrypoints.web.address=:80" # Listens for HTTP traffic on port 80
    ports:
      - "80:80"     # Main app traffic
      - "8080:8080" # Traefik Dashboard UI
    volumes:
      # Allows Traefik to read Docker events to auto-discover services
      - "/var/run/docker.sock:/var/run/docker.sock:ro" 

  # --------------------------------------------------------
  # 2. OUR APPLICATION (PREDICTION API)
  # --------------------------------------------------------
  prediction-api:
    image: traefik/whoami # Using a dummy web server for testing
    labels:
      # Tell Traefik to handle this container
      - "traefik.enable=true"
      
      # Route traffic from localhost directly to this container
      - "traefik.http.routers.predict-router.rule=Host(`localhost`)" 
      
      # Define the Rate Limiter (2 requests/sec, burst up to 5)
      - "traefik.http.middlewares.predict-limiter.ratelimit.average=2"
      - "traefik.http.middlewares.predict-limiter.ratelimit.burst=5"
      
      # Attach the Rate Limiter to our router
      - "traefik.http.routers.predict-router.middlewares=predict-limiter"
      
      # Tell Traefik which internal port the app is listening on
      - "traefik.http.services.predict-service.loadbalancer.server.port=80"
```

### Step 2: Understanding the Labels (The "Magic")
Traefik works by reading the labels attached to your application containers. Here is the breakdown of the three key concepts we used above:

* **Routers:** The rule=Host('localhost') line tells Traefik, "If a request comes in asking for 'localhost', send it to this container." In production, you will change this to Host('api.yourdomain.com').

* **Middlewares:** These are plugins that modify requests before they reach your app. We defined a middleware called predict-limiter and gave it our rate limit rules.

* **Attachment:** Creating a middleware isn't enough; you must attach it to a router using the middlewares=predict-limiter label.

### Step 3: Run and Test Locally
#### 1. Start the infrastructure
Open your terminal in the same folder as the Compose file and run:

```Bash
docker compose up -d
```

#### 2. Verify the Dashboard
Open http://localhost:8080 in your browser. You will see the Traefik UI. Navigate to the "HTTP" section to see your Routers and Middlewares actively running.

#### 3. Test the Rate Limit (The 429 Error)
Open your terminal and run a quick loop to blast the server with 10 rapid requests. You will see the first few succeed (HTTP/1.1 200 OK), and the rest instantly fail (HTTP/1.1 429 Too Many Requests), proving our server is protected.

Mac/Linux Command:

```Bash
for i in {1..10}; do curl -i http://localhost; done
```

#### Step 4: Production Checklist
Before pushing this to a live server, ensure you update the following:

* **Remove Insecure API:** Remove the - "--api.insecure=true" line from the Traefik command list so your dashboard isn't exposed to the public internet.

* **Update the Host Rule:** Change Host('localhost') to your actual production domain name.

* **Adjust Rate Limits:** Tune the average and burst limits to match your server's actual benchmarked capacity.