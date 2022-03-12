function faceCheck(n) {$.get('/person', 
	function(data) {
		if (data == 'unkown'){
			setTimeout(() => {faceCheck(3000)}, n);
		}else{
			var url = "/user/" + data
			document.body.style.animation = 'fadeOutAnimation ease 3s'
			setTimeout(() => {window.location.replace(url)}, 2900);
			
		}
    });
}



function resize_to_fit(n) {
	  document.getElementById("text").style.fontSize = (n) + "vw";

	if(n==0){
		document.getElementById("text").style.fontSize = "16px";
	}
	else if (document.getElementById("text").offsetHeight >= document.getElementById("outer").offsetHeight) {
		resize_to_fit(n-0.5);
	  }
}