import { APIProvider, Map } from "@vis.gl/react-google-maps"

export default function GoogleMap({ latitude, longitude }: { latitude: number, longitude: number }) {

  return (
    <>
      <APIProvider apiKey="AIzaSyASY_IDhXJtE2ACwRp7rE_2x99_GmtGI28">
        <Map
          defaultCenter={{ lat: latitude, lng: longitude }}
          defaultZoom={3}
          gestureHandling='greedy'
          disableDefaultUI
        />
      </APIProvider >
    </>
  )
}
