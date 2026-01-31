pub fn interpolate(x: f32, from: (f32, f32), to: (f32, f32)) -> f32 {
    let (start1, stop1) = from;
    let (start2, stop2) = to;

    ((x - start1) / (stop1 - start1)) * (stop2 - start2) + start2
}
