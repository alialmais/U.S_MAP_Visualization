from sqlalchemy import create_engine, text
import folium
from folium.plugins import MarkerCluster
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import uuid  
from config import DB_CONFIG, ADMIN_PASSWORD  

app = Flask(__name__)

# Database connection function
def get_data_from_mysql():
    engine = create_engine(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")
    query = text("""
        SELECT ID, Start_Lat, Start_Lng, Severity, State, City, Street, Year 
        FROM US_Accidents
    """)
    df = pd.read_sql(query, engine)
    return df

def get_color(severity):
    colors = {
        1: "#2ca02c",  # Green
        2: "#1f77b4",  # Blue
        3: "#ff7f0e",  # Orange
        4: "#d62728"   # Red
    }
    return colors.get(severity, "gray")  # Default to gray

def generate_map():
    data = get_data_from_mysql()
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles="CartoDB Positron")

    marker_cluster = MarkerCluster(icon_create_function=f'''
        function(cluster) {{
            var childCount = cluster.getChildCount();
            var color = "gray";  
            var textColor = "white";  

            if (childCount < 50) {{
                color = "#E0FFFF";  
                textColor = "black";  
            }} else if (childCount <= 100) {{
                color = "#ADD8E6";  
            }} else if (childCount <= 250) {{
                color = "#87CEFA";  
            }} else if (childCount <= 500) {{
                color = "#4682B4";  
            }} else if (childCount <= 1000) {{
                color = "#4169E1";  
            }} else if (childCount <= 2000) {{
                color = "#0000CD";  
            }} else if (childCount <= 5000) {{
                color = "#00008B";  
            }} else if (childCount <= 10000) {{
                color = "#191970";  
            }} else {{
                color = "#0B0B3B";  
            }}

            return new L.DivIcon({{
                html: '<div style="background-color: ' + color + '; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; color: ' + textColor + '; font-size: 14px;">' + childCount + '</div>',
                className: 'marker-cluster'
            }});
        }}
    ''')

    for _, row in data.iterrows():
        popup_content = f"""
        <div style="font-size: 14px; line-height: 1.5;">
            <b>ID:</b> {row['ID']}<br>
            <b>State:</b> {row['State']}<br>
            <b>City:</b> {row['City']}<br>
            <b>Street:</b> {row['Street']}<br>
            <b>Year:</b> {row['Year']}
        </div>
        """
        folium.CircleMarker(
            location=[row["Start_Lat"], row["Start_Lng"]],
            radius=6, 
            color=get_color(row["Severity"]),
            fill=True,
            fill_color=get_color(row["Severity"]),
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=300),
        ).add_to(marker_cluster)

    marker_cluster.add_to(m)
    return m._repr_html_()

@app.route("/")
def serve_map():
    return generate_map()  

#Route: Add Accident (Admin Only)
@app.route("/add-accident", methods=["GET", "POST"])
def add_accident():
    if request.method == "POST":
        password = request.form["password"]
        if password == ADMIN_PASSWORD:  #  Use the secure password from config.py

            accident_id = str(uuid.uuid4())  # Generates a unique accident ID automatically
            
            state = request.form["state"]
            city = request.form["city"]
            street = request.form["street"]
            severity = request.form["severity"]
            lat = request.form["lat"]
            lng = request.form["lng"]
            year = request.form["year"]
            
            #Use SQLAlchemy engine
            engine = create_engine(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")
            conn = engine.connect()

            #Check for duplicates (ID-based check)
            query = text("SELECT COUNT(*) FROM US_Accidents WHERE ID = :accident_id")
            result = conn.execute(query, {"accident_id": accident_id}).fetchone()
            if result[0] > 0:
                conn.close()
                return "❌ Sorry, this accident already exists!"

            #Insert new accident into MySQL
            query = text("""
                INSERT INTO US_Accidents (ID, Severity, Start_Lat, Start_Lng, Street, City, State, Year) 
                VALUES (:id, :severity, :lat, :lng, :street, :city, :state, :year)
            """)
            conn.execute(query, {
                "id": accident_id,
                "severity": severity,
                "lat": lat,
                "lng": lng,
                "street": street,
                "city": city,
                "state": state,
                "year": year
            })
            conn.commit()
            conn.close()

            return redirect(url_for("serve_map"))  #Refresh the map dynamically after adding
        else:
            return "❌ Unauthorized", 403  # If the password is wrong

    return render_template("add_accident.html")

#Run Flask App
if __name__ == "__main__":
    print(f"Serving map at http://127.0.0.1:5008/")  
    print(f"Admin page: http://127.0.0.1:5008/add-accident (Password Protected)")  
    app.run(port=5008, debug=True)
