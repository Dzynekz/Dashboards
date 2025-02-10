// Function to create the chart
function createChart(containerSelector, data) {
    // Select container and get its dimensions
    const container = d3.select(containerSelector).node();
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    // Define margins and compute chart dimensions
    const margin = { top: 50, right: 20, bottom: 100, left: 60 },
          width = containerWidth - margin.left - margin.right,
          height = containerHeight - margin.top - margin.bottom;

    // Remove existing SVG before redrawing
    d3.select(containerSelector).select("svg").remove();

    // Append SVG element
    const svg = d3.select(containerSelector)
        .append("svg")
        .attr("width", containerWidth)
        .attr("height", containerHeight)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add chart title
    svg.append("text")
        .attr("class", "chart-title")
        .attr("x", width / 2)
        .attr("y", -10)
        .attr("text-anchor", "middle")
        .attr("font-size", "2rem")
        .attr("font-weight", "bold")
        .text("Liczba ofert w ostatnich 7 dniach");

    // X scale using scaleBand for spacing
    const x = d3.scaleBand()
        .domain(data.map(d => d.day))
        .range([0, width])
        .padding(0.4);  // Controls spacing between bars

    // Y scale for offer count
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.offers)])
        .nice()
        .range([height, 0]);

    // Add X axis
    svg.append("g")
        .attr("transform", `translate(0, ${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
        .call(d3.axisLeft(y));

    // ** Add X-axis title **
    svg.append("text")
        .attr("class", "axis-title")
        .attr("x", width / 2)
        .attr("y", height + 60)  // Positioned below the x-axis
        .attr("text-anchor", "middle")
        .attr("font-size", "1rem")
        .text("Data");  // X-axis label text

    // ** Add Y-axis title **
    svg.append("text")
        .attr("class", "axis-title")
        .attr("x", -height / 2)  // Centered along the y-axis
        .attr("y", -40)  // Positioned left of y-axis
        .attr("transform", "rotate(-90)")  // Rotate for Y axis
        .attr("text-anchor", "middle")
        .attr("font-size", "1rem")
        .text("Liczba ofert");  // Y-axis label text

    // Draw bars
    svg.selectAll(".bar")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.day))
        .attr("y", d => y(d.offers))
        .attr("width", x.bandwidth())  // Uses scaleBand for width
        .attr("height", d => height - y(d.offers))
        .attr("fill", "#0096c7");

    // Add labels on top of bars
    svg.selectAll(".label")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "label")
        .attr("x", d => x(d.day) + x.bandwidth() / 2)
        .attr("y", d => y(d.offers) - 5)
        .attr("text-anchor", "middle")
        .attr("font-size", "12px")
        .attr("fill", "black")
        .text(d => d.offers);
}

// Example data for 7 days
const data = [
    { day: "Mon 03\n12 PM", offers: 98 },
    { day: "Tue 04\n12 PM", offers: 86 },
    { day: "Wed 05\n12 PM", offers: 68 },
    { day: "Thu 06\n12 PM", offers: 105 },
    { day: "Fri 07", offers: 111 }
];

// Create chart on page load
createChart(".weekly-chart", data);

// Redraw chart on window resize
window.addEventListener("resize", () => createChart(".weekly-chart", data));
