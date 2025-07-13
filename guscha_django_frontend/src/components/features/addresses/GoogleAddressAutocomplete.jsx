import React, { useState, useEffect, useRef } from "react";
import "../../../styles/GoogleAddressAutocomplete.css";

const GoogleAddressAutocomplete = ({
  onAddressSelect,
  placeholder = "Введите адрес..."
}) => {
  const [inputValue, setInputValue] = useState("");
  const [predictions, setPredictions] = useState([]);
  const [showPredictions, setShowPredictions] = useState(false);
  const [loading, setLoading] = useState(false);
  const autocompleteService = useRef(null);
  const sessionToken = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Initialize Google Maps services
    if (window.google && window.google.maps) {
      autocompleteService.current =
        new window.google.maps.places.AutocompleteService();
      sessionToken.current =
        new window.google.maps.places.AutocompleteSessionToken();
    }
  }, []);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    if (value.length > 2) {
      fetchPredictions(value);
    } else {
      setPredictions([]);
      setShowPredictions(false);
    }
  };

  const fetchPredictions = (input) => {
    if (!autocompleteService.current) return;

    setLoading(true);
    const options = {
      input,
      sessionToken: sessionToken.current,
      types: ["address"],
      componentRestrictions: { country: "ru" } // Ограничение по России
    };

    autocompleteService.current.getPlacePredictions(
      options,
      (predictions, status) => {
        setLoading(false);
        if (
          status === window.google.maps.places.PlacesServiceStatus.OK &&
          predictions
        ) {
          setPredictions(predictions);
          setShowPredictions(true);
        } else {
          setPredictions([]);
        }
      }
    );
  };

  const handlePredictionSelect = (prediction) => {
    setInputValue(prediction.description);
    setShowPredictions(false);

    // Get detailed place information
    const placesService = new window.google.maps.places.PlacesService(
      document.createElement("div")
    );

    const request = {
      placeId: prediction.place_id,
      fields: ["address_components", "formatted_address", "geometry"]
    };

    placesService.getDetails(request, (place, status) => {
      if (
        status === window.google.maps.places.PlacesServiceStatus.OK &&
        place
      ) {
        const addressData = parseAddressComponents(place.address_components);
        onAddressSelect(addressData);
      }
    });
  };

  const parseAddressComponents = (components) => {
    const addressData = {
      address_line1: "",
      city: "",
      state: "",
      postal_code: "",
      country: ""
    };

    components.forEach((component) => {
      const types = component.types;

      if (types.includes("street_number")) {
        addressData.address_line1 =
          component.long_name + " " + addressData.address_line1;
      }
      if (types.includes("route")) {
        addressData.address_line1 =
          addressData.address_line1 + component.long_name;
      }
      if (
        types.includes("locality") ||
        types.includes("administrative_area_level_2")
      ) {
        addressData.city = component.long_name;
      }
      if (types.includes("administrative_area_level_1")) {
        addressData.state = component.long_name;
      }
      if (types.includes("postal_code")) {
        addressData.postal_code = component.long_name;
      }
      if (types.includes("country")) {
        addressData.country = component.long_name;
      }
    });

    return addressData;
  };

  const handleBlur = () => {
    // Delay hiding predictions to allow clicking on them
    setTimeout(() => setShowPredictions(false), 200);
  };

  return (
    <div className="google-autocomplete-container">
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        className="google-autocomplete-input"
      />

      {loading && (
        <div className="autocomplete-loading">
          <div className="spinner"></div>
        </div>
      )}

      {showPredictions && predictions.length > 0 && (
        <ul className="autocomplete-predictions">
          {predictions.map((prediction) => (
            <li
              key={prediction.place_id}
              className="prediction-item"
              onClick={() => handlePredictionSelect(prediction)}
            >
              <div className="prediction-text">{prediction.description}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

// Fallback component if Google Maps is not loaded
const FallbackAddressInput = ({ onAddressSelect, placeholder }) => {
  const [value, setValue] = useState("");

  const handleChange = (e) => {
    setValue(e.target.value);
  };

  const handleBlur = () => {
    // Simple fallback - just pass the raw address
    onAddressSelect({ address_line1: value });
  };

  return (
    <input
      type="text"
      value={value}
      onChange={handleChange}
      onBlur={handleBlur}
      placeholder={placeholder}
      className="google-autocomplete-input"
    />
  );
};

// Wrapper component that checks for Google Maps
const GoogleAddressAutocompleteWrapper = (props) => {
  if (window.google && window.google.maps && window.google.maps.places) {
    return <GoogleAddressAutocomplete {...props} />;
  }
  return <FallbackAddressInput {...props} />;
};

export default GoogleAddressAutocompleteWrapper;
