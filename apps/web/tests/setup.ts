import "@testing-library/jest-dom";

// Mock window.scrollTo for jsdom environment
if (typeof window !== "undefined") {
  window.scrollTo = () => {};
}

// Mock ResizeObserver for jsdom environment (required by charts & responsive containers)
if (typeof global.ResizeObserver === "undefined") {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// Mock HTMLCanvasElement.prototype.getContext for jsdom environment (required by Apache ECharts / zrender)
if (typeof HTMLCanvasElement !== "undefined") {
  const dummyContext = new Proxy(
    {
      canvas: {} as HTMLCanvasElement,
      measureText: () => ({ width: 0, height: 0 }),
      getImageData: () => ({ data: [] }),
      createImageData: () => [],
      createLinearGradient: () => ({ addColorStop: () => {} }),
      createRadialGradient: () => ({ addColorStop: () => {} }),
      createPattern: () => ({}),
    },
    {
      get: (target, prop) => {
        if (prop in target) return (target as Record<string, unknown>)[prop as string];
        return () => {};
      },
    }
  );

  HTMLCanvasElement.prototype.getContext = (() => {
    return dummyContext;
  }) as unknown as typeof HTMLCanvasElement.prototype.getContext;
}
