# PUBG_CV_Healthbar
A Python application that uses OpenCV to detect the PUBG healthbar, and publishes health through a webservice.

![PUBG Screenshot](https://i.imgur.com/ieRC0mL.png)

# How to use with OBS Studio

* Download the latest [release](https://github.com/thegouger/PUBG_CV_Healthbar/releases/latest) and run the application
* By default the application runs a webservice at http://localhost:6969 and displays the player's health as an animated Doomguy icon
* Open OBS and add a BrowserSource to the Scene with the URL set to http://localhost:6969
* Position the BrowserSource as desired

![PUBG Screenshot](https://i.imgur.com/53FOo7W.png)

# Custom Web View

* Setting the `"CUSTOM_HTML": false` to true will serve a custom index.html, and will serve any content in images/
* Modify this index.html as desired to produce a custom OBS widget
* The web service exposes an endpoint `/health`, which doing a GET on will return the detected health
