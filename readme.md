SI507 Final Project – University of Michigan

This project models the global airline route network using real OpenFlights data.
Airports are represented as nodes, flight routes as directed edges, and the system
provides multiple tools for searching, analyzing, and visualizing the network.

Key Features
1. Load & construct a global flight network
    - Reads airports.csv and routes.csv from the OpenFlights dataset
    - Builds adjacency lists and Python objects (Airport, Route, FlightNetwork)

2. Explore individual airports
    - View airport name, city, country, coordinates
    - Show total outbound routes and sample destinations

3. Rank top airports by connectivity (hub detection)
    - Sort airports by outbound degree
    - Identify the largest global hubs

4. BFS shortest-path algorithm
    - Computes route paths with minimum number of hops
    - Includes NetworkX visualization of the subgraph of the path

5. Wikipedia integration with caching
    - Fetch additional metadata from Wikipedia (airport HTML)
    - Store results in airport_cache.json to avoid repeated downloads

6. Hub Network Visualization (Main Final Feature)
    - Plot the Top–N largest airports and the routes between them
    - Node size proportional to degree
    - Provides a clean, interpretable drawing of the backbone of global air mobility