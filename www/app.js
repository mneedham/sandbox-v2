$(document).ready(function() {

  var listener = function(event) {
    JSON.stringify(event.data);
  }
 
  if (window.addEventListener){
    addEventListener("message", listener, false)
  } else {
    attachEvent("onmessage", listener)
  }

  $('.btn-login').click(function(e) {
    window.open("https://auth.neo4j.com/index.html",
                "login");
  });

  $('.btn-logout').click(function(e) {
    e.preventDefault();
    logout();
  })

  //retrieve the profile:
  var retrieve_show_profile = function() {
    var id_token = localStorage.getItem('id_token');
    if (id_token) {
      //lock.getProfile(id_token, function (err, profile) {
        if (err) {
          return alert('There was an error getting the profile: ' + err.message);
        }
        return show_profile_info(profile);
      });
    }
  };

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
  retrieve_show_profile();
  retrieve_show_instances();
});
