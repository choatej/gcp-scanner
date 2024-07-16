# Resource Visualizer

The resource visualizer provides a visualization of a JSON tree.  It was created to view GCP resources across multiple
projects, but it can easily be extended to represent any JSON data.

The data is displayed as a collapsible tree to allow expanding and collapsing sections to avoid using up the entire
screen or requiring a lot of scrolling.

## To use the visualizer

### Prerequisites
**node >= 20.15.1**

### Running the app
1. Create a file in [public](./public) named `results.json` containing the JSON data
2. Install the dependencies
```bash
npm i
```
2. Start the node application:
```bash
npm start
```

To exit, just use ctrl-C
