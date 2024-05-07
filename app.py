import tkinter as tk
from tkinter import messagebox, scrolledtext
from py2neo import Graph
from tkinter import font


graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))


def show_most_affiliated_company():
    query = """
    MATCH (person:Person)-[r]->(company:Company)
    WITH company, COUNT(DISTINCT person) AS Affiliates
    ORDER BY Affiliates DESC
    LIMIT 1
    RETURN company.name AS CompanyName, Affiliates
    """
    execute_query(query, "Most Affiliated Company")

def show_dominant_sector():
    query = """
    MATCH (company:Company)-[:BELONGS_TO_SECTOR]->(sector:Sector)
    WITH sector, COUNT(DISTINCT company) AS Companies
    ORDER BY Companies DESC
    LIMIT 1
    RETURN sector.name AS SectorName, Companies
    """
    execute_query(query, "Biggest Sector")

def show_aggregate_statistics():
    query = """
    MATCH (sector:Sector)
    WITH COLLECT(sector.name) AS SectorNames

    MATCH (company:Company)
    WITH SectorNames, COUNT(company) AS TotalCompanies

    MATCH (director:Person)-[:BOARD_MEMBER_OF]->(company)
    WITH SectorNames, TotalCompanies, COUNT(DISTINCT director) AS TotalBoardMembers

    MATCH (chairperson:Person)<-[:CHAIRPERSON_OF]-(company)
    WITH SectorNames, TotalCompanies, TotalBoardMembers, COUNT(DISTINCT chairperson) AS TotalChairpersons

    MATCH (ceo:Person)<-[:CEO_OF]-(company)
    WITH SectorNames, TotalCompanies, TotalBoardMembers, TotalChairpersons, COUNT(DISTINCT ceo) AS TotalCEOs

    MATCH (secretary:Person)<-[:SECRETARY_OF]-(company)
    RETURN SectorNames, TotalCompanies, TotalBoardMembers, TotalChairpersons, TotalCEOs, COUNT(DISTINCT secretary) AS TotalSecretaries
    """
    execute_query(query, "Aggregate Statistics")

def show_multiple_affiliations():
    query = """
    MATCH (director:Person)-[:BOARD_MEMBER_OF]->(company:Company)
    WITH director, COUNT(DISTINCT company) AS Companies
    WHERE Companies > 1
    RETURN COLLECT(director.name) AS MultiCompanyBoardMembers
    """
    execute_query(query, "Multi-Affiliated Board Members:")

def execute_query(query, title):
    try:
        result = graph.run(query).data()
        if result:
            output = f"{title}:\n" + '\n'.join([f"{key}: {val}" for res in result for key, val in res.items()]) + "\n\n"
        else:
            output = f"{title}: No data found.\n\n"
        results_text.insert(tk.END, output)
    except Exception as e:
        results_text.insert(tk.END, f"Error fetching {title.lower()}: {str(e)}\n\n")


def find_entity():
    entity_name = search_entry.get().strip()
    entity_type = search_type.get()  # Assumes you are using radio buttons to determine this

    if entity_type == 'Person':
        query = f"""
        MATCH (p:Person)-[r]-(c:Company)
        WHERE p.name = '{entity_name}'
        RETURN p.name AS name, 
               r.positions AS positions, 
               c.name AS companyName
        """
    elif entity_type == 'Company':
        query = f"""
        MATCH (c:Company)-[:BELONGS_TO_SECTOR]->(s:Sector)
        WHERE c.name = '{entity_name}'
        RETURN c.name AS name, s.name AS sectorName
        """

    execute_query(query, f"Search for {entity_type}")


def find_shortest_path():
    from_name = from_entry.get()
    to_name = to_entry.get()
    query = f"""
    MATCH (p1:Person {{name: '{from_name}'}}), (p2:Person {{name: '{to_name}'}}),
    path = shortestPath((p1)-[*]-(p2))
    RETURN path
    """
    execute_query(query, "Shortest Path")
    
def initialize_projections():
    create_graph_query = """
    CALL gds.graph.project(
        'myGraph',
        ['Person', 'Company'],
        ['BOARD_MEMBER_OF', 'SECRETARY_OF', 'CHAIRPERSON_OF', 'CEO_OF']
    )
    YIELD graphName, nodeCount, relationshipCount
    RETURN graphName, nodeCount, relationshipCount
    """
    try:
        # Create or check the graph projection
        results = graph.run(create_graph_query).data()
    except Exception as e:
        print("Error:" , e)

def degree_centrality():
    centrality_query = """
    CALL gds.degree.stream('myGraph')
    YIELD nodeId, score
    RETURN gds.util.asNode(nodeId).name AS name, score AS degree
    ORDER BY score DESC
    LIMIT 30
    """
    try:
        #Run the centrality query
        results = graph.run(centrality_query).data()
        centrality_text.delete('1.0', tk.END)  # Clear previous results
        for result in results:
            centrality_text.insert(tk.END, f"{result['name']} degree centrality = {result['degree']}\n")
    except Exception as e:
        centrality_text.insert(tk.END, f"Error: {str(e)}\n")

def betweenness_centrality():
    try:
        # Assume the graph is already projected, as handled elsewhere
        results = graph.run("""
            CALL gds.betweenness.stream('boardMemberGraph')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS name, score AS betweenness
            ORDER BY score DESC
            LIMIT 20
        """).data()
        centrality_text.delete('1.0', tk.END)  # Clear previous results
        for result in results:
            centrality_text.insert(tk.END, f"{result['name']} betweenness centrality = {result['betweenness']}\n")
    except Exception as e:
        centrality_text.insert(tk.END, f"Error fetching board member centrality data: {str(e)}\n")


def closeness_centrality():
    results = graph.run("""
        CALL gds.closeness.stream('myGraph')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).name AS name, score AS closeness
        ORDER BY closeness DESC
        LIMIT 20
    """).data()
    centrality_text.delete('1.0', tk.END)  # Clear previous results
    try:
        for result in results:
            centrality_text.insert(tk.END, f"{result['name']} closeness centrality = {result['closeness']}\n")
    except Exception as e:
            centrality_text.insert(tk.END, f"Error fetching: {str(e)}\n")


def PageRank_centrality():
    try:
        results = graph.run("""
            CALL gds.pageRank.stream('pageRankGraph')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS name, score AS pageRank
            ORDER BY score DESC
            LIMIT 20
        """).data()
        centrality_text.delete('1.0', tk.END)  # Clear previous results
        for result in results:
            centrality_text.insert(tk.END, f"{result['name']} PageRank centrality = {result['pageRank']}\n")
    except Exception as e:
        centrality_text.insert(tk.END, f"Error fetching PageRank: {str(e)}\n")


def Link_Prediction():
    pass

#initialize_projections()
app = tk.Tk()
app.title("KSE30 Analytics")
headline_font = font.Font(family='Helvetica', size=16, weight='bold')  # Adjust font settings as needed
headline_label = tk.Label(app, text="KSE30 Stock Market Analysis", font=headline_font)
headline_label.pack(pady=10)  # Add some vertical padding
# Graph Statistics
# Scrolled Text area for displaying results
results_text = scrolledtext.ScrolledText(app, wrap=tk.WORD, height=5, width=80)
results_text.pack(padx=10, pady=10)
# Buttons frame
buttons_frame = tk.Frame(app)
buttons_frame.pack()

# Buttons for the different functions
tk.Button(buttons_frame, text="Aggregate Stats", command=show_aggregate_statistics).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Multiple Affiliations", command=show_multiple_affiliations).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Most Affiliated Co.", command=show_most_affiliated_company).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Dominant Sector", command=show_dominant_sector).pack(side=tk.LEFT, padx=5)

# Entity Search Widgets
search_frame = tk.Frame(app)
search_frame.pack()

search_type = tk.StringVar(value="Person")  # Default to 'Person'
tk.Radiobutton(search_frame, text="Person", variable=search_type, value="Person").pack(side=tk.LEFT)
tk.Radiobutton(search_frame, text="Company", variable=search_type, value="Company").pack(side=tk.LEFT)

tk.Label(app, text="Entity Name").pack()
search_entry = tk.Entry(app)
search_entry.pack()
tk.Button(app, text="Find Entity", command=find_entity).pack()

# Create a frame for the shortest path search
path_search_frame = tk.Frame(app)
path_search_frame.pack(pady=10)  # Adds some vertical padding

# Label and entry for 'From'
tk.Label(path_search_frame, text="From:").pack(side=tk.LEFT)
from_entry = tk.Entry(path_search_frame, width=20)
from_entry.pack(side=tk.LEFT, padx=5)  # Adds some padding between widgets

# Label and entry for 'To'
tk.Label(path_search_frame, text="To:").pack(side=tk.LEFT)
to_entry = tk.Entry(path_search_frame, width=20)
to_entry.pack(side=tk.LEFT, padx=5)
# Button to find the shortest path
tk.Button(app, text="Find Shortest Path", command=find_shortest_path).pack()

# Scrolled Text area for displaying centrality results
#initialize_projections()
centrality_text = scrolledtext.ScrolledText(app, wrap=tk.WORD, height=10, width=50)
centrality_text.pack(padx=10, pady=10)

# Buttons to find  Centrality

buttons_frame = tk.Frame(app)
buttons_frame.pack(pady=10)

tk.Button(buttons_frame, text="Find Degree Centrality", command=degree_centrality).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Betweenness Centrality", command=betweenness_centrality).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="Closeness Centrality", command=closeness_centrality).pack(side=tk.LEFT, padx=5)
tk.Button(buttons_frame, text="PageRank Centrality", command=PageRank_centrality).pack(side=tk.LEFT, padx=5)
tk.Button(app, text="Link Prediction", command=Link_Prediction).pack()

app.geometry("600x700")
app.mainloop()