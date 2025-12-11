import pandas as pd
from collections import defaultdict, deque


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

    def add_inbound_route(self, route):
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
    """
    def __init__(self, src, dst, airline):
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
    load_airport(airport):
        Inserts an Airport object into the network.

    load_route(route):
        Inserts a Route object into the network and updates inbound/outbound lists.

    build_adjacency():

        
    build_from_openflights(airports_csv, routes_csv, airlines_csv=None):
        Constructs Airport and Route objects directly from OpenFlights CSV files.

    summarize_airport(code):

    
    get_airport(code):
    
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

            if src in self.airports and dst in self.airports:
                key = (src, dst, airline)
                if key not in self.routes:
                    route = Route(src, dst, airline)
                    self.routes[key] = route

                    src_airport = self.airports[src]
                    dst_airport = self.airports[dst]

                    src_airport.add_outbound_route(route)
                    dst_airport.add_inbound_route(route)

        print("routes:", len(self.routes))


    def build_adjacency(self):
        self.adjacency = defaultdict(set)
        for route in self.routes.values():
            self.adjacency[route.src].add(route.dst)


    def build_from_openflights(self, airports_csv, routes_csv, airlines_csv = None):
        self.load_airports(airports_csv)
        self.load_routes(routes_csv)
        self.build_adjacency()


    def summarize_airport(self, code):
        """
        Return a human-readable summary for an airport code.
        Includes basic airport info + number of routes + sample destinations.

        Parameters
        ----------
        code : str
            IATA code, e.g. "LAX", "DTW".

        Returns
        -------
        str or None
            Summary text, or None if airport not found.
        """

        airport = self.get_airport(code)
        if airport is None:
            return None

        # Out going route (from adjacency)
        outgoing = self.adjacency.get(code, set())

        dest_names = []
        for dst_id in list(outgoing)[:5]:
            if dst_id in self.airports:
                dest_names.append(self.airports[dst_id].name)

        summary = (
            f"Airport: {airport.name} ({airport.code})\n"
            f"City: {airport.city}, Country: {airport.country}\n"
            f"Latitude, Longtitude: {airport.lat}, {airport.lon}\n"
            f"Code: {airport.code}\n"
            f"Total outgoing routes: {len(outgoing)}\n"
            f"Sample destinations: {', '.join(dest_names) if dest_names else 'None'}"
        )

        return summary


    def get_airport(self, code):
        """
        Safely retrieve an Airport object by its IATA code.

        Parameters
        ----------
        code : str
            The IATA airport code (e.g., "LAX", "DTW").

        Returns
        -------
        Airport or None
            The Airport object if found, otherwise None.
        """
        if code is None:
            return None

        norm_code = code.strip().upper()

        return self.airports.get(norm_code, None)
    

    def find_shortest_path_bfs(self, src_code: str, dst_code: str) -> list[str] | None:
        """
        Find the shortest path (in number of hops) between two airports
        using Breadth-First Search (BFS).

        Parameters
        ----------
        src_code : str
            IATA code for the source airport, e.g. "LAX".
        dst_code : str
            IATA code for the destination airport, e.g. "DTW".

        Returns
        -------
        list[str] or None
            A list of IATA codes representing the path from source to
            destination (inclusive), or None if no path is found.
        """
        if src_code is None or dst_code is None:
            return None

        src = src_code.strip().upper()
        dst = dst_code.strip().upper()

        if self.get_airport(src) is None or self.get_airport(dst) is None:
            return None

        if src == dst:
            return [src]

        visited = set()
        parent: dict[str, str] = {}
        q = deque()

        visited.add(src)
        q.append(src)

        found = False

        while q:
            current = q.popleft()
            for neighbor in self.adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    if neighbor == dst:
                        found = True
                        q.append(neighbor)
                        break
                    q.append(neighbor)
            if found:
                break

        if not found:
            return None

        path = [dst]
        while path[-1] != src:
            prev = parent[path[-1]]
            path.append(prev)

        path.reverse()
        return path


    def format_path(self, path: list[str] | None) -> str:
        """
        Format a path (list of IATA codes) into a human-readable string.

        Parameters
        ----------
        path : list[str] or None
            Path returned by find_shortest_path_bfs.

        Returns
        -------
        str
        """
        if not path:
            return "No path found."

        lines = []
        lines.append(f"Path length (hops): {len(path) - 1}")
        segments = []

        for code in path:
            airport = self.get_airport(code)
            if airport is not None:
                segments.append(f"{code} ({airport.city}, {airport.country})")
            else:
                segments.append(code)

        lines.append(" -> ".join(segments))
        return "\n".join(lines)



if __name__ == "__main__":
    net = FlightNetwork()
    net.load_airports("data/airports.csv")
    net.load_routes("data/routes.csv")
    net.build_adjacency()

    print(len(net.airports))
    print(len(net.routes))