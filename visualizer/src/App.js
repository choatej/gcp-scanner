import React, { useEffect, useState } from 'react';
import './App.css';
// import ReactJson from "@microlink/react-json-view";

function App() {
  const [jsonData, setJsonData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/results.json'); // Fetch from public folder
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        setJsonData(data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  if (!jsonData) {
    return <div>Loading...</div>;
  }
  return (
    // <ReactJson
    //     src={jsonData}
    //     name={"projects"}
    //     theme={"brewer"}
    //     iconStyle={"square"}
    //     indentWidth={4}
    //     collapsed={true}
    //     displayObjectSize={false}
    //     displayDataTypes={false}
    //     sortKeys={true}
    // />
      ""
  );
}

export default App;
