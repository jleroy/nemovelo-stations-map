const timeunits = {
    year  : 24 * 60 * 60 * 1000 * 365,
    month : 24 * 60 * 60 * 1000 * 365/12,
    day   : 24 * 60 * 60 * 1000,
    hour  : 60 * 60 * 1000,
    minute: 60 * 1000,
    second: 1000
}

function getJSON(url, callback, callback_arg=undefined) {
    // Init XMLHttpRequest().
    const xhr = new XMLHttpRequest();
    // HTTP GET request to the specified URL.
    xhr.open('GET', url, true);
    // Force to handle response as JSON.
    xhr.responseType = 'json';
    // Callback function to call when server response is received.
    xhr.onload = function() {
        if (xhr.status === 200) {
            // Return JSON data to callback function.
            if (callback_arg) {
                callback(xhr.response, callback_arg);
            } else {
                callback(xhr.response);
            }
        } else {
            // Log error in browser console.
            console.log('Error trying to get JSON file "' + url + '": ' +
                    'HTTP ' + xhr.status + '.');
        }
    };
    // Fire request.
    xhr.send();
};

function refreshMap(geojson, old_datetime) {
    // Convert GeoJSON last update property to a Date() object.
    const new_datetime = new Date(geojson.last_updated);
    
    // Only refresh if the GeoJSON file has been updated in order to avoid
    // redirect loops.
    if (old_datetime.getTime() !== new_datetime.getTime()) {
        // Refresh page.
        window.location.reload();
    }    
}

function convertToRelativeTime(now, elapsed) {
    // Init RelativeTimeFormat. Force French locale.
    const rtf = new Intl.RelativeTimeFormat('fr-FR', {
        numeric: 'auto',
        style: 'long',
    });
    
    // Convert milliseconds to seconds/minutes/hours/...
    for (const unit in timeunits) {
        if (Math.abs(elapsed) > timeunits[unit] || unit == 'second') {
            // -120000 => '2 minutes ago'.
            return rtf.format(Math.round(elapsed/timeunits[unit]), unit);
        }
    }
}

function setLastUpdate(geojson) {
    // Convert GeoJSON last update property to a Date() object.
    const datetime = new Date(geojson.last_updated);
    // Current date/time.
    const now = new Date();
    // Elapsed time since last GeoJSON file update, in milliseconds.
    const elapsed = datetime - now;
    
    // More than 5 minutes since last GeoJSON file update? We refresh the page.
    if (elapsed <= -300000) {
        // Check that the device is still connected to the Internet before
        // reloading the page in order to avoid damage user experience on mobile
        // devices.
        getJSON('/stations.geojson', refreshMap, datetime);
    }
    
    // Update interface with relative time since last update, in human-readable
    // format.
    document.getElementById('last_update').innerHTML = 'Mis à jour ' + 
            convertToRelativeTime(now, elapsed);
    
    // We refresh the information every 5 seconds.
    setTimeout(setLastUpdate, 5000, geojson);
}

document.addEventListener('DOMContentLoaded', function() {
    // Show time since last GeoJSON file update when DOM is ready.
    getJSON('/stations.geojson', setLastUpdate);
});
