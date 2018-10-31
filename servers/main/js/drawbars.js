function put_new_confidence(val){
  console.log("draw to chart: " + val);
  move_n = move_n + 1;
  g_confidences[move_n] = Math.round(val * 10) / 10;
    chart.load({
        columns:[g_confidences]
    });
} // end function


$(function(){ 
  // "global parameter"
  move_n = 0;
  g_confidences = [];
  for (var i=1; i<31;i++){
    g_confidences.push(-1);
  } // end for

  var x = ['x'];
  var thr = ['thr'];
  for (var i=1; i<31;i++){
    x.push(i);
    thr.push(50);
  } // end for
  var chart_data = [x, thr];
  // generate the chart
  chart = c3.generate({
    bindto: '#chart_area',
    legend: { show: false },
    data: {
      x: 'x',
      columns: chart_data,
      type: 'bar',
      types: {
        confidence: 'bar',
        thr: 'line',
      },
    },
    bar: {
      width: {
        ratio: 0.8
       }
    }
  });
  chart.axis.max({y: 90});
  chart.axis.min({y: 10});
});

