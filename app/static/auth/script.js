$(document).ready(function () {
  $("#province").on("change", function () {
    let province_id = $(this).val();
    $("#municipality").addClass("disabled");
    $("#barangay").addClass("disabled");

    if (province_id) {
      let selectedMunicipality = "{{ request.form['municipality'] }}";
      $.get(
        "/get_municipalities",
        { province_id: province_id },
        function (data) {
          $("#municipality").html(
            '<option value="">Select Municipality</option>'
          );
          $("#municipality").val("");
          $("#barangay").html('<option value="">Select Barangay</option>');
          $("#barangay").val("");
          data.forEach(function (municipality) {
            const isSelected =
              String(municipality.municipality_id) === selectedMunicipality;
            console.log(
              `${isSelected} = ${String(
                municipality.municipality_id
              )} = ${selectedMunicipality}`
            );
            $("#municipality").append(
              `<option value="${municipality.municipality_id}" ${
                String(municipality.municipality_id) == selectedMunicipality
                  ? "selected"
                  : ""
              }>${municipality.municipality_name}</option>`
            );
          });
          $("#municipality").removeClass("disabled");
        }
      );
    }
  });

  $("#municipality").on("change", function () {
    let municipality_id = $(this).val();

    $("#barangay").addClass("disabled");

    if (municipality_id) {
      let selectedBarangay = "{{ request.form['barangay'] }}";
      $.get(
        "/get_barangays",
        { municipality_id: municipality_id },
        function (data) {
          $("#barangay").html('<option value="">Select Barangay</option>');
          $("#barangay").val("");
          data.forEach(function (barangay) {
            console.log();
            $("#barangay").append(
              `<option value="${barangay.barangay_id}"  ${
                barangay.barangay_id == selectedBarangay ? "selected" : ""
              }>${barangay.barangay_name}</option>`
            );
          });
          $("#barangay").removeClass("disabled");
        }
      );
    }
  });
});
