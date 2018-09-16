import json
import pandas as pd

from statsbomb.utils import columns, get_event_name


class Events:
    """
    Parses json data into tabular format for a particular event.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = json.load(open(self.file_path))
        self.match_id = self.file_path.split('/')[-1].split('.json')[0]

    def __repr__(self):
        return 'Events for match ID {}'.format(self.match_id)

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.data)

    def get_dataframe(self, event_type: str) -> pd.DataFrame:

        assert event_type.title() in columns['events'], '`{}` is not a valid event type'.format(event_type)

        # get all events for a given event type
        all_events = [i for i in self.data if i['type']['name'] == event_type.title()]
        assert len(all_events) > 0, 'Found 0 events for `{}`'.format(event_type)

        # get common attributes
        common_elements = [{key: event.get(key, None) for key in columns['common']} for event in all_events]

        # get attributes specific to this event type
        event_objects = []
        for event in all_events:
            object_dict = {}
            for key in columns[event_type]:
                try:
                    object_dict[key] = event[event_type.replace(' ', '_')].get(key, None)
                except KeyError:
                    object_dict[key] = None
            event_objects.append(object_dict)

        final = [{**i, **j} for i, j in zip(common_elements, event_objects)]

        # combine all into one dataframe and order columns
        df = pd.DataFrame(final)
        df['event_type'] = event_type
        df = df[['event_type'] + columns['common'] + columns[event_type]]

        # get names from attributes of form: `{"id" : 7, "name" : "From Goal Kick"}`
        name_cols = [i for i in df.columns if i in columns['name_cols']]
        df[name_cols] = df[name_cols].applymap(get_event_name)

        # split location arrays into their own columns
        try:
            df[['start_location_x', 'start_location_y']] = df['location'].apply(pd.Series)
        except ValueError:
            pass
        df = df.drop('location', axis=1)

        # only the shot event type has a z coordinate
        if 'end_location' in df.columns:
            try:
                df[['end_location_x', 'end_location_y', 'end_location_z']] = df['end_location'].apply(pd.Series)
            except ValueError:
                df[['end_location_x', 'end_location_y']] = df['end_location'].apply(pd.Series)
            df = df.drop('end_location', axis=1)

        return df
