function faceCheck(n) {
	$.get('/person',
	function(data) {
		var path = window.location.pathname;
		var page = path.split("/").pop();
		if (data == page){
			setTimeout(() => {faceCheck(n)}, n);
		}else{
			var url = "/user/" + data
			window.location.replace(url)
		}
    });
}

$(document).keydown(function(e) {
      switch(e.which) {
          case 84: // T
			  window.location.replace("/selector");
          break;

         default: return;
     }
     e.preventDefault();
  });