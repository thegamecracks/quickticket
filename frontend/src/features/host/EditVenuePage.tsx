import { useParams } from 'react-router';
import VenueEditorPage from './VenueForm';

export default function EditVenuePage() {
  const { id } = useParams<{ id: string }>();

  return <VenueEditorPage venueId={id ?? ''} />;
}
