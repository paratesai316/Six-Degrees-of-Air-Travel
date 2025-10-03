# ✈️ Global Flight Network Explorer

An interactive web application for visualizing and analyzing the global air travel network. Built with Python and Dash, this project explores the "small-world" phenomenon in air travel, allowing users to find optimal routes, explore all possible connections, and view the entire flight network in real-time.

## ✨ Key Features

This application provides four distinct modes for exploring the global flight network, each offering a unique perspective on global connectivity.

### 🌐 Full Network View
An interactive macro-view of the entire flight network. A dynamic slider allows you to filter the density of the network in real-time, moving from a clean overview of only the most connected international hubs to the full, intricate web of all available routes. Airport hubs are sized and colored based on their "degree"—the number of direct destinations they serve—making it easy to identify critical nodes in global travel infrastructure.

### ✈️ Optimal Route Finder
This powerful tool calculates and compares the two best paths between any two airports, highlighting a fundamental trade-off in travel planning:

- **Least Flights (BFS):** This route, found using a Breadth-First Search, guarantees the minimum number of takeoffs and landings, often representing the simplest itinerary for a traveler.

- **Shortest Distance (Dijkstra):** This route, calculated using Dijkstra's algorithm, finds the path that covers the minimum total kilometers. This often represents the most fuel-efficient or fastest route in terms of pure flight time, even if it requires an extra connection.

### 🔍 All Routes Explorer
Go beyond the "best" path and discover every possible way to get from A to B. This mode finds and displays every unique route between two airports for a given number of flights (up to 3, to manage computational load). The results are drawn on the map and presented in a detailed list, including the specific airlines for each leg of the journey, sorted by the shortest total distance.

### 📍 Single Airport Explorer
Zoom in on a single airport to instantly see all of its direct, outgoing flight paths displayed on the map. This provides a clear, focused visualization of an airport's reach and its role as either a local spoke or a major international hub.

---

## 🚀 How to Run the Web Application

1. **Clone the Repository**  
   ```bash
   git clone [https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git](https://github.com/paratesai316/Six-Degrees-of-Air-Travel.git)
   cd Six-Degrees-of-Air-Travel

2. **Install Dependencies**

   Install all necessary Python libraries using the `requirements.txt` file. This ensures your environment matches the one used for development.
   ```bash
   pip install -r requirements.txt

3. **Set Up Local Data (Optional but Recommended)**
   This project is significantly enhanced by a local, more comprehensive dataset which provides a richer and more accurate network model.
   Create a folder named data in the project's root directory.
   Place your `local_data_airports.dat`, `local_data_airlines.dat`, and `local_data_routes.dat` files inside it.
   If these files are not found, the application will gracefully fall back to using the default, less extensive online dataset.

4. **Run the Application**
   Execute the main application script from your terminal:
   ```bash
   python 6_multi_modal_flight_map.py
   ```
   The application will be available at http://127.0.0.1:8050/


## 🔬 Project Evolution & Static Analysis

This project began as a series of static Python scripts designed to answer the core question: "What is the average number of flights that need to be taken to fly between any two random airports?" This initial exploration evolved into the full interactive application. The code for these foundational analyses can be found in the src/static_analysis/ directory.

## 📊 Visualizations
#1: Unweighted Analysis

Below are visualizations for the unweighted analysis of flight distribution and the directed graph of the flight network:

<img src="https://github.com/paratesai316/Six-Degrees-of-Air-Travel/blob/main/Outputs/1_unweighted_flight_distribution.png" alt="Unweighted Flight Distribution" style="max-width:50%; height:auto;" /> 
#2: Unweighted Analysis:

Below are visualizations for the unweighted analysis of flight distribution and the directed graph of the flight network:

<img src="https://github.com/paratesai316/Six-Degrees-of-Air-Travel/blob/main/Outputs/2_unweighted_digraph_flight_distribution.png" alt="Unweighted Directed Graph Flight Distribution" style="max-width:50%; height:auto;" />
#3: Population-Weighted Flights

This image visualizes the flight distribution weighted by population. It gives an insight into the connectivity of airports based on the populations they serve:

<img src="https://github.com/paratesai316/Six-Degrees-of-Air-Travel/blob/main/Outputs/3_population_weighted_flight_distribution.png" alt="Population Weighted Flight Distribution" style="max-width:50%; height:auto;" />
#4: Population-Weighted Distance

This chart displays the distance distribution, weighted by population, offering an analysis of travel distances adjusted for population density:

<img src="https://github.com/paratesai316/Six-Degrees-of-Air-Travel/blob/main/Outputs/4_population_weighted_distance_distribution.png" alt="Population Weighted Distance Distribution" style="max-width:50%; height:auto;" />

##

Feel free to explore the visualizations and interact with the web application to get a deeper understanding of global air travel networks.



