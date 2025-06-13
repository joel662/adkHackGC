import React from 'react';
import { render, act, screen, fireEvent } from '@testing-library/react-native';
import { Alert } from 'react-native';
import App from './index';
import { csvData } from '../../synthetic_telematics_data'; // Assuming this is a valid import for test purposes
import haversine from 'haversine-distance';
import { StyleSheet } from 'react-native';


// Mock the necessary modules and functions
jest.mock('react-native-maps', () => {
  const MockMapView = () => React.createElement('View', { testID: 'MapView' });
  const MockPolyline = () => React.createElement('View', { testID: 'Polyline' });
  const MockMarker = () => React.createElement('View', { testID: 'Marker' });

  return {
    __esModule: true,
    default: MockMapView,
    Polyline: MockPolyline,
    Marker: MockMarker,
  };
});

jest.mock('@react-native-picker/picker', () => {
  const MockPicker = ({ selectedValue, onValueChange, children }) => (
    <React.Fragment>
      <button testID="picker" onPress={() => onValueChange(selectedValue === 'route1' ? 'route2' : 'route1')}>
        {selectedValue === null ? 'Select a route' : `Route ${selectedValue}`}
      </button>
      {children}
    </React.Fragment>
  );

  MockPicker.Item = ({ label, value }) => <button testID={`picker-item-${value}`}>{label}</button>;
  return {
    __esModule: true,
    Picker: MockPicker,
  };
});

jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));


const mockFetch = (data: any) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve(data),
    })
  ) as jest.Mock;
};


const mockHaversine = (distance:number) => {
    (haversine as jest.Mock).mockImplementation(() => distance)
}


const mockCsvData = `
route_id,timestamp,latitude,longitude,speed_kmph,acceleration_mps2,gyroscope_yaw,gyroscope_roll
1,2024-01-01T00:00:00Z,43.7315,-79.7624,50,0,0,0
1,2024-01-01T00:00:10Z,43.7316,-79.7625,60,1,1,1
`;

describe('App Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    (Alert.alert as jest.Mock).mockClear();
    mockFetch({
      features: [
        {
          geometry: {
            coordinates: [[-79.7624, 43.7315], [-79.7625, 43.7316]],
          },
          properties: { route_id: 'route1' },
        },
      ],
    });
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.clearAllMocks();
    delete global.fetch;
  });

  it('renders the map and picker', async () => {
    render(<App />);
    await act(async () => {
        jest.runAllTimers(); // ensures useEffect runs
    });
    expect(screen.getByTestID('MapView')).toBeTruthy();
    expect(screen.getByTestID('picker')).toBeTruthy();
  });

  it('fetches route data on mount', async () => {
    render(<App />);
    await act(async () => {
      jest.runAllTimers();
    });
    expect(global.fetch).toHaveBeenCalledWith(
      'https://services3.arcgis.com/rl7ACuZkiFsmDA2g/arcgis/rest/services/Transit_Stops_and_Routes/FeatureServer/1/query?outFields=*&where=1%3D1&f=geojson'
    );
  });

  it('updates busRoutes when route data is fetched', async () => {
    render(<App />);
    await act(async () => {
      jest.runAllTimers();
    });

    expect(screen.getByTestID('picker-item-route1')).toBeTruthy();
  });

  it('handles route selection from picker', async () => {
    render(<App />);
    await act(async () => {
      jest.runAllTimers();
    });

    fireEvent.press(screen.getByTestID('picker'));
    expect(screen.getByTestID('picker').props.children).toBe('Route route2');
  });


  it('starts simulation when button is pressed', async () => {
      // Mock successful fetch and csv data
      mockFetch({
          features: [
              {
                  geometry: { coordinates: [[-79.7624, 43.7315], [-79.7625, 43.7316]] },
                  properties: { route_id: 'route1' },
              },
          ],
      });
      (csvData as any) = mockCsvData; // Directly assign to the mocked csvData
      render(<App />);
      await act(async () => {
          jest.runAllTimers();
      });
      fireEvent.press(screen.getByTestID('picker'));
      fireEvent.press(screen.getByTestID('button'));

      expect(Alert.alert).not.toHaveBeenCalled();
  });


  it('calls Alert.alert when no route data is found in startSimulation', async () => {
    // Mock successful fetch, but return no route
    mockFetch({ features: [] });
    (csvData as any) = mockCsvData; // Directly assign to the mocked csvData
    render(<App />);
    await act(async () => {
      jest.runAllTimers();
    });
    fireEvent.press(screen.getByTestID('picker'));
    fireEvent.press(screen.getByTestID('button'));

    expect(Alert.alert).toHaveBeenCalledWith('Error', 'Selected route data not found.');
  });


  it('calls Alert.alert when no simulation data is available', async () => {
    mockFetch({
        features: [
            {
                geometry: { coordinates: [[-79.7624, 43.7315], [-79.7625, 43.7316]] },
                properties: { route_id: 'route1' },
            },
        ],
    });
    (csvData as any) = '';
    render(<App />);
    await act(async () => {
        jest.runAllTimers();
    });

    fireEvent.press(screen.getByTestID('picker'));
    fireEvent.press(screen.getByTestID('button'));

    expect(Alert.alert).toHaveBeenCalledWith('Error', 'No simulation data available.');
  });

  it('calculates route distances correctly', () => {
    const { calculateRouteDistances } = require('./index'); // Direct import for testing
    mockHaversine(1000);
    const coordinates = [{ latitude: 43.7315, longitude: -79.7624 }, { latitude: 43.7316, longitude: -79.7625 }];
    const result = calculateRouteDistances(coordinates);
    expect(result.distances).toEqual([1000]);
    expect(result.totalDistance).toBe(1000);
  });

  it('gets position along route correctly', () => {
    const { getPositionAlongRoute } = require('./index');
    const coordinates = [
      { latitude: 0, longitude: 0 },
      { latitude: 1, longitude: 1 },
    ];
    const distances = [100];
    const distanceTraveled = 50;
    const result = getPositionAlongRoute(coordinates, distances, distanceTraveled);
    expect(result).toEqual({ latitude: 0.5, longitude: 0.5 });
  });

  it('gets last coordinate if distance traveled exceeds route length', () => {
      const { getPositionAlongRoute } = require('./index');
      const coordinates = [
          { latitude: 0, longitude: 0 },
          { latitude: 1, longitude: 1 },
      ];
      const distances = [100];
      const distanceTraveled = 150;
      const result = getPositionAlongRoute(coordinates, distances, distanceTraveled);
      expect(result).toEqual({ latitude: 1, longitude: 1 });
  });
});