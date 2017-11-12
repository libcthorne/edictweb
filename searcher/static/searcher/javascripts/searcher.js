console.log("Hello?");

$(document).ready(function() {
  $('#id_query').autocomplete({
    serviceUrl: '/api/entries/',
    dataType: 'json',
    paramName: 'query',
    transformResult: function(response) {
      return {
	suggestions: $.map(response.results, function(dataItem) {
	  return {
	    value: dataItem.edict_data,
	    data: dataItem.edict_data,
	  };
	})
      };
    }
  })
});
