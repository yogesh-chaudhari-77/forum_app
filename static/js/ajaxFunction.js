/*  [8]
    AJAX - Browser Support - Tutorialspoint
    AJAX - Browser Support - Tutorialspoint (2021). Available at: https://www.tutorialspoint.com/ajax/ajax_browser_support.htm (Accessed: 3 March 2021).
*/

//Browser Support Code
function ajaxFunction() {
    var ajaxRequest;  // The variable that makes Ajax possible!
    try {
        // Opera 8.0+, Firefox, Safari 
        ajaxRequest = new XMLHttpRequest();
        return ajaxRequest;
    } catch (e) {

        // Internet Explorer Browsers
        try {
            ajaxRequest = new ActiveXObject("Msxml2.XMLHTTP");
            return ajaxRequest;
        } catch (e) {

            try {
                ajaxRequest = new ActiveXObject("Microsoft.XMLHTTP");
                return ajaxRequest;
            } catch (e) {

                // Something went wrong
                alert("Your browser broke!");
                return false;
            }
        }
    }
}

// Use this method for any server calls
function send_request(ajaxRequest, method, url, data, additional_headers) {
    ajaxRequest.open(method, url, true);
    ajaxRequest.send(data);
}

