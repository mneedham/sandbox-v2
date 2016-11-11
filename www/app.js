$(document).ready(function() {

  var listener = function(event) {
    JSON.stringify(event.data);
    event.source.close();
  }
 
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  var pollInterval;

  $('.btn-login').click(function (e) {
    win = window.open("https://auth.neo4j.com/index.html",
                "loginWindow",
                "location=0,status=0,scrollbars=0, width=1080,height=720");
    try {
      win.moveTo(500, 300);
    } catch (e) {
    }
    window.addEventListener('message', function(event) {
      clearInterval(pollInterval);
    });
    pollInterval = setInterval(function (e) {
      win.postMessage('Polling for results', 
                      "https://auth.neo4j.com/index.html")
      }, 6000);
  });

  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })

  var show_profile_info = function(profile) {
     $('.nickname').text(profile.nickname);
     $('.btn-login').hide();
     $('.avatar').attr('src', profile.picture).show();
     $('.btn-logout').show();
  };

  var retrieve_show_instances = function() {
    var id_token = localStorage.getItem('id_token');
    $.getJSON("https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetRunningInstancesForUser?auth0_key=mykey", function(data) {
      show_instances(data);
    }); 
  }

  var show_instances = function(instances) {
    alert(JSON.stringify(instances));
  }

  var logout = function() {
    localStorage.removeItem('id_token');
    window.location.href = "/";
  };

  // Display user information
  retrieve_show_instances();
});
