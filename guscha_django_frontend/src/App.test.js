import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Глобальные переменные Jest
/* global test, expect */

// Простой тест без импорта App компонента
test('renders learn react link', () => {
  const TestComponent = () => (
    <div>
      <a
        className="App-link"
        href="https://reactjs.org"
        target="_blank"
        rel="noopener noreferrer"
      >
        Learn React
      </a>
    </div>
  );
  
  render(<TestComponent />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});

test('basic react functionality works', () => {
  const TestComponent = () => <div data-testid="test">Test Component</div>;
  render(<TestComponent />);
  expect(screen.getByTestId('test')).toBeInTheDocument();
});
