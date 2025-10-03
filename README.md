✈️ Global Flight Network Explorer
An interactive web application for visualizing and analyzing the global air travel network. Built with Python and Dash, this project explores the "small-world" phenomenon in air travel, allowing users to find optimal routes, explore all possible connections, and view the entire flight network in real-time.

✨ Key Features
This application provides four distinct modes for exploring the global flight network:

🌐 Full Network View: An interactive overview of the entire flight network. A dynamic slider allows you to filter the density of the network, from showing only major international hubs to revealing the full, complex web of connections. Airport hubs are sized and colored based on the number of destinations they serve.

✈️ Optimal Route Finder: Calculates and compares the two best paths between any two airports:

Least Flights (BFS): The route with the minimum number of stops.

Shortest Distance (Dijkstra): The route that covers the minimum total kilometers.

🔍 All Routes Explorer: Finds and displays every possible route between two airports for a given number of flights (up to 3). The results are displayed on the map and in a list sorted by the shortest total distance.

📍 Single Airport Explorer: Select any airport to instantly see all of its direct, outgoing flight paths displayed on the map, providing a clear view of that airport's connectivity.

🚀 How to Run the Web Application
1. Clone the Repository
git clone [https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git](https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git)
cd Six-Degrees-of-Air-Travel

2. Install Dependencies
Install all necessary Python libraries using the requirements.txt file.

pip install -r requirements.txt

3. Set Up Local Data (Optional)
This project is enhanced by a local, more comprehensive dataset.

Create a folder named data in the project's root directory.

Place your local_data_airports.dat, local_data_airlines.dat, and local_data_routes.dat files inside it.
(If these files are not found, the application will gracefully fall back to using the default online dataset.)

4. Run the Application
Execute the main application script from your terminal:

python 6_multi_modal_flight_map.py

The application will be available at http://127.0.0.1:8050/.

🔬 Project Evolution & Static Analysis
This project began as a series of static Python scripts to analyze the "six degrees of separation" concept and evolved into the full interactive application. The code for these initial analyses can be found in the src/static_analysis/ directory.

The foundational analysis progressed through several models:

Model 1 & 2: A baseline analysis using an unweighted graph and Breadth-First Search (BFS) to find the minimum number of flights between random airports.

Model 3: A more realistic simulation that introduces a population bias to the random sampling, modeling real-world travel demand.

Model 4: The most advanced static model, which constructs a distance-weighted graph and combines the population bias with Dijkstra's algorithm to find the shortest possible travel distance in kilometers.

Static Analysis Results
The visual outputs from these initial scripts are saved in the outputs/ folder.

Unweighted Flight Distribution

Population-Weighted Flights

Population-Weighted Distance







🛠️ Tech Stack & Data Sources
Technology: Python, Dash, Plotly, NetworkX, Pandas

Base Data: OpenFlights.org - The foundational public database of airports and routes.

Local Data (Optional): A user-provided, more comprehensive dataset of airports, airlines, and routes that can be merged with the base data for a richer analysis.