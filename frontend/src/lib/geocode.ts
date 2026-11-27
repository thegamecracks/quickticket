import type { Point } from './types';

type GeocodingLibrary = NonNullable<ReturnType<typeof import('@vis.gl/react-google-maps').useMapsLibrary<'geocoding'>>>;

/** Structured address fields recovered from a geocoder result. */
export type GeocodedAddress = {
  streetAddress: string;
  unit: string;
  city: string;
  province: string;
  postalCode: string;
  country: string;
};

/**
 * Geocodes an address to a (lat, lng) pair. Geocoding failures
 * fall back to null so callers can still save their records.
 */
export async function geocodeAddress(library: GeocodingLibrary, address: string): Promise<Point | null> {
  try {
    const { results } = await new library.Geocoder().geocode({ address });
    const loc = results[0]?.geometry.location;

    if (!loc) console.warn('Geocode returned no results for:', address);

    return loc ? { lat: loc.lat(), lng: loc.lng() } : null;
  } catch (error) {
    console.error('Geocoding failed for:', address, error);
    return null;
  }
}

/**
 * Reverse geocodes coordinates into structured address fields.
 */
export async function reverseGeocodeCoords(library: GeocodingLibrary, point: Point): Promise<GeocodedAddress | null> {
  try {
    const { results } = await new library.Geocoder().geocode({
      location: { lat: point.lat, lng: point.lng },
    });

    const components: { long_name: string; types: string[] }[] = results[0]?.address_components ?? [];
    const find = (types: string[]): string =>
      components.find((component) => component.types.some((type) => types.includes(type)))?.long_name ?? '';

    const streetAddress = [find(['street_number']), find(['route'])].filter(Boolean).join(' ');

    return {
      streetAddress,
      unit: find(['subpremise']),
      city: find(['locality', 'administrative_area_level_3', 'postal_town']),
      province: find(['administrative_area_level_1']),
      postalCode: find(['postal_code']),
      country: find(['country']),
    };
  } catch (error) {
    console.error('Reverse geocoding failed for:', point, error);
    return null;
  }
}
