import { sixteenthsToFraction } from './decimalToFraction';

export function getDisplayString(amount, unit, conversion = null, scale = 1) {
    const data = getRawMath(amount, unit, conversion, scale);
    return `${sixteenthsToFraction(data.amount)} ${data.unit}`;
}

export function getRawMath(amount, unit, conversion = null, scale = 1) {
    let finalAmount = amount * scale;
    let finalUnit = unit;

    if (conversion) {
        // Handle if your backend sends an object: { amount: 6.09, unit: 'fl oz' }
        if (typeof conversion === 'object' && conversion.amount && unit == "unit") {
            finalAmount = amount * conversion.amount * scale;
            finalUnit = conversion.unit;
        }
        // Handle if your backend sends a raw string from the backfill script: "6.09 fl oz"
        else if (typeof conversion === 'string') {
            const match = conversion.match(/^([\d.]+)\s+(.*)$/);
            if (match) {
                finalAmount = amount * parseFloat(match[1]) * scale;
                finalUnit = match[2];
            }
        }
    }

    if (finalUnit.search("tsp") != -1 && finalAmount > 3) {
        finalUnit = "tbsp";
        finalAmount /= 3;
    }

    return { amount: finalAmount, unit: finalUnit };
}