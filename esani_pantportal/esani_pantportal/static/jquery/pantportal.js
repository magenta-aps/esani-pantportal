function updateQueryString(key, value) {
    if (history.pushState) {
        let searchParams = new URLSearchParams(window.location.search);
        searchParams.set(key, value);
        let newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?' + searchParams.toString();
        window.history.pushState({path: newurl}, '', newurl);
    }
}

function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return false;
};


function queryParams(params){  // Kaldes af bootstrap-table fordi vi peger på den med data-query-params
    if (params["offset"] < 0) {
        params["offset"] = 0;
    }
    // Bootstrap takes care of these parameters for us.
    const keys_to_ignore = ["limit", "offset", "search", "sort", "order"];
    const search_data = JSON.parse($("#search_data").text());
    for (let key in search_data) {
        if (keys_to_ignore.includes(key) == false) {
            params[key] = search_data[key];
        }
    }
    return params;
}

$(document).ready(
    function () {
        // Clicking a `download-excel` link adds `?format=excel` to the current page URL
        $("a.download-excel").click(
            function () {
                let searchParams = new URLSearchParams(window.location.search);
                searchParams.set("format", "excel");
                window.location.search = searchParams.toString();
            }
        )
    }
);
