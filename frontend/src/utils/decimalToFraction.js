export function sixteenthsToFraction(n) {
    if(!n) 
        return "";
    
    let whole = Math.floor(n), dec = n - whole;
    let num = Math.round(dec * 16), denom = 16;

    if(num == 0)
        return whole != 0 ? whole.toString() : "";
    
    if(num == 16)
        return (whole + 1).toString();

    while (num % 2 == 0) {
        num >>= 1;
        denom >>= 1;
    }

    const fractions = {
        '1/2': '½', 
        '1/4': '¼', '3/4': '¾',
        '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞',
        '1/16': '¹⁄₁₆', '3/16': '³⁄₁₆', '5/16': '⁵⁄₁₆', '7/16': '⁷⁄₁₆', '9/16': '⁹⁄₁₆', '11/16': '¹¹⁄₁₆', '13/16': '¹³⁄₁₆', '15/16': '¹⁵⁄₁₆'
    };

    let unicodeFraction = fractions[`${num}/${denom}`];

    return (whole !== 0 ? `${whole}  ` : '') + unicodeFraction;
}