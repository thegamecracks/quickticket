import { APIProvider, Map, AdvancedMarker } from "@vis.gl/react-google-maps"

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";
const MAP_KEY = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID ?? "";

export default function GoogleMap({ latitude, longitude }: { latitude: number, longitude: number }) {

  return (
    <APIProvider apiKey={API_KEY}>
      <Map
        mapId={MAP_KEY}
        style={{ width: "100%", height: "20rem" }}
        defaultCenter={{ lat: latitude, lng: longitude }}
        defaultZoom={14}
        gestureHandling='greedy'
      >
        <AdvancedMarker position={{ lat: latitude, lng: longitude }} />
      </Map>
    </APIProvider >
  )
}
