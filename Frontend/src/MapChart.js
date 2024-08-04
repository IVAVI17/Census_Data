import React, { useState } from "react";
import DatamapsIndia from "react-datamaps-india";
import axios from "axios";
import "./MapChart.css"; 

const MapChart = () => {
  const [hoveredState, setHoveredState] = useState("");
  const [topLanguages, setTopLanguages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleHover = async (stateName) => {
    if (stateName !== hoveredState) {
      setHoveredState(stateName);
      setLoading(true);
      try {
        const response = await axios.post(
          "http://127.0.0.1:8000/most_spoken_languages/",
          {
            state_name: stateName,
            num_languages: 3,
          },
          {
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        setTopLanguages(response.data.top_languages);
      } catch (error) {
        console.error("Error fetching languages:", error);
      }
      setLoading(false);
    }
  };

  return (
    <div className="map-chart-container">
      <DatamapsIndia
        style={{ position: "relative", left: "25%" }}
        regionData={{
          "Andaman & Nicobar Island": { value: 150 },
          "Andhra Pradesh": { value: 470 },
          "Arunanchal Pradesh": { value: 248 },
          Assam: { value: 528 },
          Bihar: { value: 755 },
          Chandigarh: { value: 95 },
          Chhattisgarh: { value: 1700 },
          Delhi: { value: 1823 },
          Goa: { value: 508 },
          Gujarat: { value: 624 },
          Haryana: { value: 1244 },
          "Himachal Pradesh": { value: 640 },
          "Jammu & Kashmir": { value: 566 },
          Jharkhand: { value: 814 },
          Karnataka: { value: 2482 },
          Kerala: { value: 899 },
          Lakshadweep: { value: 15 },
          "Madhya Pradesh": { value: 1176 },
          Maharashtra: { value: 727 },
          Manipur: { value: 314 },
          Meghalaya: { value: 273 },
          Mizoram: { value: 306 },
          Nagaland: { value: 374 },
          Odisha: { value: 395 },
          Puducherry: { value: 245 },
          Punjab: { value: 786 },
          Rajasthan: { value: 1819 },
          Sikkim: { value: 152 },
          "Tamil Nadu": { value: 2296 },
          Telangana: { value: 467 },
          Tripura: { value: 194 },
          "Uttar Pradesh": { value: 2944 },
          Uttarakhand: { value: 1439 },
          "West Bengal": { value: 1321 }
        }}
        hoverComponent={({ value }) => {
          handleHover(value.name);
          return (
            <div className="hover-info">
              <div className="state-info">
                {value.name} {value.value}
              </div>
              {loading && hoveredState === value.name ? (
                <div className="loading-indicator">Loading...</div>
              ) : (
                hoveredState === value.name && topLanguages.length > 0 && (
                  <div className="languages-info">
                    <h3>Top 3 Most Spoken Languages in {hoveredState}</h3>
                    <ul>
                      {topLanguages.map((language, index) => (
                        <li key={index}>
                          {language["Mother tongue name"]}: {language["Urban P"]}
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              )}
            </div>
          );
        }}
        mapLayout={{
          title: "State Wise Distribution of the Top 3 languages Spoken",
          startColor: "#b3d1ff",
          endColor: "#005ce6",
          hoverTitle: "Count",
          noDataColor: "#f5f5f5",
          borderColor: "#8D8D8D",
          hoverColor: "#0080ff",
          hoverBorderColor: "green",
          height: 500,
          weight: 300
        }}
      />
    </div>
  );
};

export default MapChart;
