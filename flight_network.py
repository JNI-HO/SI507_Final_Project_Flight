import pandas as pd
from collections import defaultdict


class Airport:
    """
    Represents an airport (node) in the Airline Route Network.

    Each Airport object stores basic metadata (name, location, identifiers)
    and maintains a record of its inbound and outbound routes. It acts as a 
    central unit for network-based analysis, such as hub detection, 
    centrality calculations, and disruption impact assessment.

    Attributes
    ----------
    code : str
        The IATA airport code (e.g., "LAX", "JFK"). This is used as the unique identifier.
    name : str
        Full airport name, such as "Los Angeles International Airport".
    city : str
        The city where the airport is located.
    country : str
        The country where the airport is located.
    lat : float
        Latitude of the airport.
    lon : float
        Longitude of the airport.

    in_routes : list of Route
        A list of Route objects representing all incoming routes (destinations → this airport).
    out_routes : list of Route
        A list of Route objects representing all outgoing routes (this airport → destinations).

    degree_in : int or None
        Number of inbound edges; computed later (optional).
    degree_out : int or None
        Number of outbound edges; computed later.
    betweenness : float or None
        Betweenness centrality value assigned later through network analysis.
    resilience_score : float or None
        Optional metric used to represent how robust this airport is in the 
        face of route disruptions or network fragmentation.
    """
    def __init__(self, code, name, city, country, lat, lon):
        self.code = code
        self.name = name
        self.city = city
        self.country = country
        self.lat = lat
        self.lon = lon
        self.out_routes = []
        self.in_routes = []
        self.degree_in = None
        self.degree_out = None
        self.betweenness = None
        self.resilience_score = None
    

    def dd_inbound_route(self, route):
        """Register a Route object as an inbound connection to this airport."""
        self.in_routes.append(route)


    def add_outbound_route(self, route):
        """Register a Route object as an outbound connection from this airport."""
        self.out_routes.append(route)


class Route:
    """
    Represents a directed airline route (edge) connecting two airports.

    A Route object stores the structural definition of a route—its origin,
    destination, and operating airline—and also provides a container for 
    statistical attributes (delay, cancellation rate, flight counts) 
    derived from BTS/On-Time Performance data. This allows network edges 
    to be enriched with performance characteristics for resilience analysis.

    Attributes
    ----------
    src : str
        IATA code of the origin airport.
    dst : str
        IATA code of the destination airport.
    airline : str
        Airline code operating this route (e.g., "DL", "UA").
    distance : float or None
        Flight distance if available (optional). May be filled in later.

    flight_count : int or None
        Number of flights observed in the BTS dataset for this route.
    avg_delay : float or None
        Average departure delay (in minutes) for the route.
    cancel_rate : float or None
        Proportion of flights canceled on this route.
    weather_cancel_rate : float or None
        Optional metric if weather-specific cancellations are incorporated.

    weight : float or None
        A scalar used for pathfinding or optimization; may combine distance,
        delay, or cancellation metrics depending on the analysis design.
    is_high_risk : bool
        Whether the route is considered high-risk (e.g., cancel_rate > threshold).
    active : bool
        Whether this route is “active” in the network (used during simulation).
    """
    def __init__(self, src, dst, airline, distance=None):
        self.src = src
        self.dst = dst
        self.airline = airline


class FlightNetwork:
    """
    A container class that manages the entire airline route network.

    This class maintains collections of Airport and Route objects, constructs 
    the adjacency structure needed for network analysis, and provides tools for 
    integrating BTS on-time performance statistics, computing centrality 
    measures, and simulating disruptions.

    Attributes
    ----------
    airports : dict[str, Airport]
        Mapping from IATA code to Airport object.
    routes : dict[tuple(str, str, str), Route]
        Mapping from (src, dst, airline) → Route object.
        Keys allow multiple airlines to operate the same pair of airports.

    adjacency : dict[str, set[str]]
        A simpler adjacency list (src → set of dst airport codes) used for BFS, 
        pathfinding, or unweighted analysis.

    Methods
    -------
    add_airport(airport):
        Inserts an Airport object into the network.

    add_route(route):
        Inserts a Route object into the network and updates inbound/outbound lists.

    build_from_openflights(airports_csv, routes_csv, airlines_csv=None):
        Constructs Airport and Route objects directly from OpenFlights CSV files.

    load_bts_statistics(bts_df):
        Integrates aggregated BTS flight-level statistics into corresponding Route objects.

    get_neighbors(airport_code):
        Returns all outbound neighbors of a given airport.

    find_path_bfs(start, end):
        Computes the shortest path (in number of hops) between two airports.

    simulate_disruption(threshold):
        Deactivates routes whose cancel_rate exceeds a threshold and recomputes 
        network connectivity or resilience metrics.

    compute_centrality():
        Computes degree-based or network-centrality metrics for all airports.
    """
    def __init__(self):
        self.airports = {}
        self.routes = {}
        self.adjacency = {}
        
    def load_airports(self, airports_csv):
        """
        Load airports from CSV and create Airport objects.
        Only airports with valid IATA codes should be included.
        """    
        # Read airports.csv
        airport_df = pd.read_csv(airports_csv)
        airport_df = airport_df[airport_df["IATA"].notna() & (airport_df["IATA"] != r"\N")]

        self.airports = {}

        for _, row in airport_df.iterrows():
            code = row["IATA"]
            airport = Airport(
                code=code,
                name=row["Name"],
                city=row["City"],
                country=row["Country"],
                lat=float(row["Latitude"]),
                lon=float(row["Longitude"]),
            )
            self.airports[code] = airport

        print("nodes (airports):", len(self.airports))

    def load_routes(self, routes_csv):
        """
        Load routes from CSV and create Route objects.
        Validate that both src and dst airport codes exist in self.airports.
        Update inbound/outbound relationships and adjacency list.
        """
        # Read routes.csv
        routes_df = pd.read_csv(routes_csv)

        # Drop source/dest airport IATA = NA
        routes_df = routes_df[
            routes_df["Source Airport"].notna()
            & routes_df["Destination Airport"].notna()
            & (routes_df["Source Airport"] != r"\N")
            & (routes_df["Destination Airport"] != r"\N")]

        self.routes = {}

        for _, row in routes_df.iterrows():
            src = row["Source Airport"]
            dst = row["Destination Airport"]
            airline = row["Airline"]

            # 確保兩邊都在 airports_dict 裡
            if src in self.airports and dst in self.airports:
                key = (src, dst, airline)
                if key not in self.routes:
                    route = Route(src, dst, airline)
                    self.routes[key] = route

        print("routes:", len(self.routes))


    def build_adjacency(self):
        self.adjacency = defaultdict(set)
        for route in self.routes.values():
            if route.active:
                self.adjacency[route.src].add(route.dst)


    def build_from_openflights(self, airports_csv, routes_csv, airlines_csv = None):
        self.load_airports(airports_csv)
        self.load_routes(routes_csv)
        self.build_adjacency()


if __name__ == "__main__":
    net = FlightNetwork()
    net.load_airports("data/airports.csv")
    net.load_routes("data/routes.csv")
    net.build_adjacency()

    print(len(net.airports))
    print(len(net.routes))