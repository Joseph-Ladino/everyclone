export function getOptimalImage(url, width, height = null) {
    if (!url) return '';

    // Check if it's an EveryPlate CDN URL. If it's a random external link, just return it safely.
    if (!url.includes('media.everyplate.com')) 
        return url;

    // Start building our custom parameter block
    let params = `c_fill,f_auto,q_auto,fl_lossy,w_${width}`;

    // Height is optional. If left out, the CDN will auto-scale the height to preserve aspect ratio
    if (height) {
        params += `,h_${height}`;
    }

    // Use regex to swap out their hardcoded parameters with our optimized ones
    // $1 is 'media.everyplate.com/' and $3 is '/everyplate_s3'
    return url.replace(/(media\.everyplate\.com\/)(.*?)(\/everyplate_s3)/, `$1${params}$3`);
}