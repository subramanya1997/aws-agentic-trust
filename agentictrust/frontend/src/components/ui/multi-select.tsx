import React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  selected: string[];
  onChange: (values: string[]) => void;
  heightClass?: string; // Tailwind height e.g. h-48
}

export function MultiSelect({ options, selected, onChange, heightClass = "h-48" }: MultiSelectProps) {
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <ScrollArea className={`border rounded-md ${heightClass}`}>
      <div className="p-2 space-y-2">
        {options.map((opt) => (
          <div key={opt.value} className="flex items-center space-x-2">
            <Checkbox
              id={`ms-${opt.value}`}
              checked={selected.includes(opt.value)}
              onCheckedChange={() => toggle(opt.value)}
            />
            <Label htmlFor={`ms-${opt.value}`} className="text-sm cursor-pointer truncate">
              {opt.label}
            </Label>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
} 