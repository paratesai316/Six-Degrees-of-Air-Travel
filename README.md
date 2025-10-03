✈️ Global Flight Network Explorer
An interactive web application for visualizing and analyzing the global air travel network. Built with Python and Dash, this project explores the "small-world" phenomenon in air travel, allowing users to find optimal routes, explore all possible connections, and view the entire flight network in real-time.

Note: You should replace app_screenshot.png with an actual screenshot of your running application.

✨ Key Features
This application provides four distinct modes for exploring the global flight network, each offering a unique perspective on global connectivity.

🌐 Full Network View: An interactive macro-view of the entire flight network. A dynamic slider allows you to filter the density of the network in real-time, moving from a clean overview of only the most connected international hubs to the full, intricate web of all available routes. Airport hubs are sized and colored based on their "degree"—the number of direct destinations they serve—making it easy to identify critical nodes in global travel infrastructure.

✈️ Optimal Route Finder: This powerful tool calculates and compares the two best paths between any two airports, highlighting a fundamental trade-off in travel planning:

Least Flights (BFS): This route, found using a Breadth-First Search, guarantees the minimum number of takeoffs and landings, often representing the simplest itinerary for a traveler.

Shortest Distance (Dijkstra): This route, calculated using Dijkstra's algorithm, finds the path that covers the minimum total kilometers. This often represents the most fuel-efficient or fastest route in terms of pure flight time, even if it requires an extra connection.

🔍 All Routes Explorer: Go beyond the "best" path and discover every possible way to get from A to B. This mode finds and displays every unique route between two airports for a given number of flights (up to 3, to manage computational load). The results are drawn on the map and presented in a detailed list, including the specific airlines for each leg of the journey, sorted by the shortest total distance.

📍 Single Airport Explorer: Zoom in on a single airport to instantly see all of its direct, outgoing flight paths displayed on the map. This provides a clear, focused visualization of an airport's reach and its role as either a local spoke or a major international hub.

🚀 How to Run the Web Application
1. Clone the Repository
git clone [https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git](https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git)
cd Six-Degrees-of-Air-Travel

2. Install Dependencies
Install all necessary Python libraries using the requirements.txt file. This ensures your environment matches the one used for development.

pip install -r requirements.txt

3. Set Up Local Data (Optional but Recommended)
This project is significantly enhanced by a local, more comprehensive dataset which provides a richer and more accurate network model.

Create a folder named data in the project's root directory.

Place your local_data_airports.dat, local_data_airlines.dat, and local_data_routes.dat files inside it.
If these files are not found, the application will gracefully fall back to using the default, less extensive online dataset.

4. Run the Application
Execute the main application script from your terminal:

python 6_multi_modal_flight_map.py

The application will be available at http://127.0.0.1:8050/.

🔬 Project Evolution & Static Analysis
This project began as a series of static Python scripts designed to answer the core question: "What is the average number of flights that need to be taken to fly between any two random airports?" This initial exploration evolved into the full interactive application. The code for these foundational analyses can be found in the src/static_analysis/ directory.

The Foundational Scripts & Results
The foundational analysis progressed through four models of increasing complexity, with each one building upon the last to create a more realistic simulation. The results from each script are visualized below. These can be run using the run_static_analysis.bat file.

#1 & #2: Unweighted Analysis

#3: Population-Weighted Flights

#4: Population-Weighted Distance







Goal: Find the average number of flights between completely random airports.
Method: An unweighted graph and Breadth-First Search (BFS).
Limitation: This model treats a flight from a tiny regional airport the same as a flight from a major hub like London Heathrow, which doesn't reflect real-world travel patterns.

Goal: Model real-world travel patterns by giving airports in populous cities a higher chance of being selected.
Method: Weighted random sampling based on city population.
Improvement: This produces a more realistic distribution of path lengths, as most journeys start or end in major metropolitan areas.

Goal: Find the average shortest travel distance (km) between population-weighted airports.
Method: A distance-weighted graph and Dijkstra's algorithm.
Improvement: This moves beyond simply counting flights to analyze the actual efficiency of the routes in terms of geographical distance covered.

🛠️ Tech Stack & Data Sources
Technology: Python, Dash, Plotly, NetworkX, Pandas

Base Data: OpenFlights.org - The foundational public database of airports and routes, used as a reliable fallback.

Local Data (Optional): A user-provided, more comprehensive dataset of airports, airlines, and routes that can be merged with the base data for a richer and more accurate analysis.

💡 Key Findings
The global flight network exhibits strong small-world properties. The fact that most airports can be connected in just a handful of flights has profound implications, demonstrating not only the efficiency of global transport but also the potential for rapid global transmission of information or disease.

When weighting for population, the average number of connections decreases. This confirms that the hub-and-spoke system is highly effective at connecting the places where most people live. Major hubs like Dubai, Atlanta, and Singapore act as powerful "super-connectors," making the world feel even smaller for the average traveler.

The "Optimal Route Finder" often shows that the path with the fewest flights is not always the one that covers the shortest geographical distance. This highlights the complex trade-offs in airline logistics, where it can be more efficient to fly a slightly longer distance through a major hub rather than taking a more direct but less-trafficked route.
