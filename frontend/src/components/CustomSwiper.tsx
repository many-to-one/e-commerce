import React, { useState, useRef, useEffect } from "react";

interface CustomSwiperProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  autoLoop?: boolean;
  interval?: number;
}

const CustomSwiper = <T,>({
  items,
  renderItem,
  autoLoop = false,
  interval = 3000,
}: CustomSwiperProps<T>) => {
  const [current, setCurrent] = useState(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const next = () => setCurrent((prev) => (prev + 1) % items.length);
  const prev = () => setCurrent((prev) => (prev - 1 + items.length) % items.length);
  const goTo = (index: number) => setCurrent(index);

  useEffect(() => {
    if (autoLoop) {
      timeoutRef.current && clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(next, interval);
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [current, autoLoop, interval]);

  return (
    <div className="relative w-full overflow-hidden">
      <div
        className="flex transition-transform duration-500 ease-in-out"
        style={{
          transform: `translateX(-${current * 100}%)`,
          width: `${items.length * 100}%`,
        }}
      >
        {items.map((item, index) => (
          <div
            key={index}
            className="flex-none w-full flex justify-center items-center"
            onClick={() => goTo(index)} // navigate to current element
          >
            {renderItem(item, index)}
          </div>
        ))}
      </div>

      {/* Controls */}
      <button
        onClick={prev}
        className="absolute left-0 top-1/2 -translate-y-1/2 bg-black/50 text-white px-3 py-1 rounded-r"
      >
        ‹
      </button>
      <button
        onClick={next}
        className="absolute right-0 top-1/2 -translate-y-1/2 bg-black/50 text-white px-3 py-1 rounded-l"
      >
        ›
      </button>

      {/* Dots */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-2">
        {items.map((_, index) => (
          <button
            key={index}
            onClick={() => goTo(index)}
            className={`w-3 h-3 rounded-full ${
              index === current ? "bg-green-500" : "bg-gray-300"
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default CustomSwiper;
