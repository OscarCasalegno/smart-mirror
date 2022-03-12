function faceCheck(n) {
	$.get('/person', 
	function(data) {
		if (data =='no_face'){
			setTimeout(() => {faceCheck(0)}, n);
		}else{
			var url = "/user/" + data
			window.location.replace(url)
		}
    });
}