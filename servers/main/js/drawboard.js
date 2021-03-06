function draw_board(state_in){
//  console.log(state_in);
  var state = JSON.parse(state_in);
//  var state = state_in;

  var cell_width   = 70;
  var cell_height  = 70;
  var stone_radius = 30;
  var color_dict= {"1":'black', "-1":'white'};

  var cell_template  = '<rect class="cell" x="@x" y="@y" width="@width" height="@height" fill="rgb(0, 153, 51)" stroke-width="2" stroke="black" title="@title" onclick="play_move(@i, @j);"/>';
  var stone_template = '<circle class="stone" label="@i, @j" cx="@x" cy="@y" r="@radius" stroke="black" stroke-width="2" fill="@color"/>';

  var p = state.length;
  var q = state[0].length;
  board_width  = p*cell_width;
  board_height = q*cell_height;


  var content = "";
  // draw board
  for (var i=0; i<p; ++i){
    for (var j=0; j<q; ++j){
      var _x = i*cell_width;
      var _y = j*cell_height;
      var line = cell_template.replace('@width', cell_width).replace('@height', cell_height).replace('@x', _x).replace('@y', _y);
      line = line.replace("@i", i).replace("@j", j);
      content = content + line;
    } // end for
  } // end for

  // draw stones
  for (var i=0; i<p; ++i){
    for (var j=0; j<q; ++j){
      var s = state[i][j];
      if (s == 0){
        continue;
      } // end if
      var _x = i* cell_width +  cell_width/2;
      var _y = j*cell_height + cell_height/2;
      var line = stone_template.replace('@x', _x).replace('@y', _y).replace('@radius', stone_radius).replace('@color', color_dict[s]);
      content = content + line;
    } // end for
  } // end for


  var header = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" height="@board_height" width="@board_width">';
  header = header.replace('@board_width', board_width).replace('@board_height', board_height);
  var footer = '</svg>';

  var output = header+content+footer;
  return output;
} // end function
