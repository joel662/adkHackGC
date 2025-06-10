import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react-native';
import userEvent from '@testing-library/user-event';
import { StyleSheet, Platform } from 'react-native';
import App from '../App';
import { csvData } from '../../synthetic_telematics_data';
import haversine from 'haversine-distance';

// Mocking necessary modules and functions
jest.mock('react-native-maps', () => {
  const MockMapView = ({ children, ...props }: any) => (
    <>{children}</>
  ); // Simplified mock, assumes no actual map functionality is needed.
  const MockPolyline = ({ ...props }: any) => <></>;
  const MockMarker = ({ ...props }: any) => <></>;

  return {
    __esModule: true,
    default: MockMapView,
    Polyline: MockPolyline,
    Marker: MockMarker,
  };
});

jest.mock('@react-native-picker/picker', () => {
  const MockPicker = ({ onValueChange, selectedValue, children, ...props }: any) => (
    <>{children}</>
  ); // Simplified mock for Picker
  const MockItem = ({ label, value, ...props }: any) => (
    <>{label}</>
  );

  return {
    __esModule: true,
    Picker: MockPicker,
    Item: MockItem,
  };
});

// Mocking the fetch function
global.fetch = jest.fn();

// Mocking the haversine function
jest.mock('haversine-distance', () =>
  jest.fn().mockImplementation((start, end) => {
    return 1000; // Mock distance for testing
  })
);


// Helper function to create a simple route object
const createRoute = (routeId: string, coordinates: { latitude: number; longitude: number }[]) => ({
  routeId,
  coordinates,
});

// Helper function to simulate a timeout for testing async operations
const flushPromises = () => new Promise(setImmediate);


describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks(); // Clear mocks before each test
    (fetch as jest.Mock).mockResolvedValue({
      json: () => ({
        features: [
          {
            properties: { route_id: '1' },
            geometry: {
              type: 'LineString',
              coordinates: [[-79.7624, 43.7315], [-79.7600, 43.7300]],
            },
          },
          {
            properties: { route_id: '2' },
            geometry: {
              type: 'LineString',
              coordinates: [[-79.7624, 43.7315], [-79.7600, 43.7300]],
            },
          },
        ],
      }),
    });
  });

  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText('Select a route')).toBeDefined();
  });

  it('fetches route data on mount and updates state', async () => {
    render(<App />);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Route 1')).toBeDefined();
      expect(screen.getByText('Route 2')).toBeDefined();
    });

  });

  it('handles route selection and updates the map', async () => {
    render(<App />);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    await waitFor(() => {
      userEvent.press(screen.getByText('Select a route'));
    });

    await waitFor(() => {
      userEvent.press(screen.getByText('Route 1'));
    });

    expect(screen.getByText('Start Simulation')).toBeEnabled();
  });

  it('starts the simulation when the button is pressed', async () => {
    render(<App />);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    await waitFor(() => {
      userEvent.press(screen.getByText('Select a route'));
    });
    await waitFor(() => {
      userEvent.press(screen.getByText('Route 1'));
    });

    await waitFor(() => {
      userEvent.press(screen.getByText('Start Simulation'));
    });
  });

  it('calculates route distances correctly', () => {
    const { calculateRouteDistances } = require('../App');
    const coordinates = [
      { latitude: 43.7315, longitude: -79.7624 },
      { latitude: 43.7300, longitude: -79.7600 },
    ];
    const result = calculateRouteDistances(coordinates);
    expect(result.distances.length).toBe(1);
    expect(result.totalDistance).toBe(1000); // Mocked value from haversine
  });

  it('gets the position along the route correctly', () => {
    const { getPositionAlongRoute } = require('../App');
    const coordinates = [
      { latitude: 0, longitude: 0 },
      { latitude: 1, longitude: 1 },
    ];
    const distances = [1000];
    const distanceTraveled = 500;
    const position = getPositionAlongRoute(coordinates, distances, distanceTraveled);
    expect(position.latitude).toBe(0.5);
    expect(position.longitude).toBe(0.5);
  });

  it('handles the simulation step correctly', async () => {
    const { getPositionAlongRoute, calculateRouteDistances } = require('../App');
    const { render, screen, act, waitFor } = require('@testing-library/react-native');
    const userEvent = require('@testing-library/user-event').default;
    const mockHaversine = require('haversine-distance');
    const appModule = require('../App');
    const App = appModule.default;
    const mockSetMarkerPosition = jest.fn();

    // Mock simulation data and route setup
    const mockRoute = createRoute('1', [{ latitude: 0, longitude: 0 }, { latitude: 1, longitude: 1 }]);
    const mockDistances = [1000];
    const mockSimulationData = [{ timestamp: '2024-01-01T00:00:00Z', speed_kmph: '10', cumulativeDistance: 0 }, { timestamp: '2024-01-01T00:00:10Z', speed_kmph: '10', cumulativeDistance: 0 }];
    jest.spyOn(appModule, 'calculateRouteDistances').mockReturnValue({ distances: mockDistances, totalDistance: 1000 });
    jest.spyOn(appModule, 'getPositionAlongRoute').mockReturnValue({ latitude: 0.5, longitude: 0.5 });

    jest.spyOn(global, 'setTimeout').mockImplementation((callback: () => void, delay: number) => {
      callback();
      return 1 as any;
    });
    jest.spyOn(global, 'clearTimeout').mockImplementation((timeoutId: number) => { });

    // Mock the use of refs
    const useRefMock = (initialValue: any) => ({
      current: initialValue,
    });

    // Override react's useRef with the mock
    const originalUseRef = React.useRef;
    (React.useRef as any) = useRefMock;
    let renderedComponent: any;

    // Render the component
    await act(async () => {
      renderedComponent = render(<App />);
      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
      await waitFor(() => {
        userEvent.press(screen.getByText('Select a route'));
      });
      await waitFor(() => {
        userEvent.press(screen.getByText('Route 1'));
      });
    });

    // Find the button to start the simulation
    const startSimulationButton = screen.getByText('Start Simulation');

    // Trigger the start simulation
    await act(async () => {
      userEvent.press(startSimulationButton);
    });
    await waitFor(() => {
    });


    // Restore useRef
    (React.useRef as any) = originalUseRef;

    jest.clearAllMocks();
    (global.setTimeout as jest.Mock).mockClear();
    (global.clearTimeout as jest.Mock).mockClear();
    jest.restoreAllMocks();
  });
  it('handles edge cases in simulationStep gracefully', async () => {
    const { getPositionAlongRoute, calculateRouteDistances } = require('../App');
    const { render, screen, act, waitFor } = require('@testing-library/react-native');
    const userEvent = require('@testing-library/user-event').default;
    const mockHaversine = require('haversine-distance');
    const appModule = require('../App');
    const App = appModule.default;
    const mockSetMarkerPosition = jest.fn();

    // Mock simulation data and route setup
    const mockRoute = createRoute('1', [{ latitude: 0, longitude: 0 }, { latitude: 1, longitude: 1 }]);
    const mockDistances = [1000];
    const mockSimulationData = [{ timestamp: '2024-01-01T00:00:00Z', speed_kmph: '10', cumulativeDistance: 0 }, { timestamp: '2024-01-01T00:00:10Z', speed_kmph: '10', cumulativeDistance: 0 }];
    jest.spyOn(appModule, 'calculateRouteDistances').mockReturnValue({ distances: mockDistances, totalDistance: 1000 });
    jest.spyOn(appModule, 'getPositionAlongRoute').mockReturnValue({ latitude: 0.5, longitude: 0.5 });

    jest.spyOn(global, 'setTimeout').mockImplementation((callback: () => void, delay: number) => {
      callback();
      return 1 as any;
    });
    jest.spyOn(global, 'clearTimeout').mockImplementation((timeoutId: number) => { });

    // Mock the use of refs
    const useRefMock = (initialValue: any) => ({
      current: initialValue,
    });

    // Override react's useRef with the mock
    const originalUseRef = React.useRef;
    (React.useRef as any) = useRefMock;
    let renderedComponent: any;

    // Render the component
    await act(async () => {
      renderedComponent = render(<App />);
      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
      await waitFor(() => {
        userEvent.press(screen.getByText('Select a route'));
      });
      await waitFor(() => {
        userEvent.press(screen.getByText('Route 1'));
      });
    });

    // Find the button to start the simulation
    const startSimulationButton = screen.getByText('Start Simulation');

    // Trigger the start simulation
    await act(async () => {
      userEvent.press(startSimulationButton);
    });
    await waitFor(() => {
    });


    // Restore useRef
    (React.useRef as any) = originalUseRef;

    jest.clearAllMocks();
    (global.setTimeout as jest.Mock).mockClear();
    (global.clearTimeout as jest.Mock).mockClear();
    jest.restoreAllMocks();
  });


  it('handles errors when fetching route data', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch'));
    const { getByText } = render(<App />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(getByText('Error')).toBeDefined();
    });
  });

  it('handles invalid CSV data in parseCSV', () => {
    const { parseCSV } = require('../App');
    const result = parseCSV('');
    expect(result).toEqual([]);
  });

  it('handles invalid route geometry in fetchRouteData', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      json: () => ({
        features: [
          {
            properties: { route_id: '3' },
            geometry: null, // Invalid geometry
          },
        ],
      }),
    });

    render(<App />);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByText('Route 3')).toBeNull();
    });
  });
});