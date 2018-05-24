// Copyright 2014 M. Rizky Luthfianto.
// Licensed under the MIT license (http://opensource.org/licenses/MIT)
// This file may not be copied, modified, or distributed
// except according to those terms.

use nalgebra::DMat;

lazy_static! {

// taken from https://github.com/seqan/seqan/blob/master/include%2Fseqan%2Fscore%2Fscore_matrix_data.h#L806
    static ref ARRAY: [i32;729]=[
         6,  -3,  -6,  -3,  -2,  -7,  -1,  -6,  -4,  -5,  -6,  -5,  -4,  -3,  -3,  -1,  -3,  -6,   0,   0,  -3,  -2, -12,  -7,  -2,  -3, -15,
        -3,   6, -11,   6,   2,  -9,  -2,  -1,  -5,  -7,  -2,  -8,  -8,   6,  -4,  -6,  -2,  -6,  -1,  -2,  -4,  -7,  -9,  -6,   1,  -4, -15,
        -6, -11,   9, -12, -12, -11,  -8,  -7,  -5,  -9, -12, -13, -12,  -9,  -8,  -7, -12,  -7,  -2,  -7,  -8,  -5, -14,  -3, -12,  -8, -15,
        -3,   6, -12,   7,   3, -13,  -3,  -3,  -6,  -9,  -4, -11,  -9,   2,  -5,  -7,  -2,  -9,  -3,  -4,  -5,  -7, -13, -10,   2,  -5, -15,
        -2,   2, -12,   3,   7, -12,  -3,  -4,  -5,  -7,  -4,  -8,  -6,  -1,  -4,  -5,   2,  -8,  -4,  -5,  -4,  -6, -15,  -8,   6,  -4, -15,
        -7,  -9, -11, -13, -12,   9,  -8,  -5,  -2,  -2, -12,  -2,  -3,  -8,  -7,  -9, -11,  -8,  -6,  -8,  -7,  -7,  -4,   2, -12,  -7, -15,
        -1,  -2,  -8,  -3,  -3,  -8,   6,  -8,  -9,  -9,  -6,  -9,  -7,  -2,  -4,  -5,  -6,  -8,  -1,  -5,  -4,  -5, -13, -12,  -4,  -4, -15,
        -6,  -1,  -7,  -3,  -4,  -5,  -8,   9,  -8,  -7,  -5,  -5,  -9,   1,  -4,  -3,   1,  -1,  -5,  -6,  -4,  -6,  -6,  -3,   0,  -4, -15,
        -4,  -5,  -5,  -6,  -5,  -2,  -9,  -8,   8,   4,  -5,  -1,   0,  -4,  -4,  -7,  -7,  -5,  -6,  -2,  -4,   2, -12,  -5,  -5,  -4, -15,
        -5,  -7,  -9,  -9,  -7,  -2,  -9,  -7,   4,   4,  -6,   3,   1,  -5,  -5,  -7,  -6,  -7,  -7,  -4,  -5,   0,  -9,  -6,  -6,  -5, -15,
        -6,  -2, -12,  -4,  -4, -12,  -6,  -5,  -5,  -6,   6,  -7,  -1,   0,  -4,  -6,  -2,   1,  -3,  -2,  -4,  -8, -10,  -8,  -3,  -4, -15,
        -5,  -8, -13, -11,  -8,  -2,  -9,  -5,  -1,   3,  -7,   7,   1,  -6,  -5,  -6,  -4,  -8,  -7,  -6,  -5,  -2,  -5,  -6,  -6,  -5, -15,
        -4,  -8, -12,  -9,  -6,  -3,  -7,  -9,   0,   1,  -1,   1,  11,  -7,  -4,  -7,  -3,  -3,  -5,  -3,  -4,  -1, -11, -10,  -4,  -4, -15,
        -3,   6,  -9,   2,  -1,  -8,  -2,   1,  -4,  -5,   0,  -6,  -7,   7,  -3,  -5,  -3,  -5,   0,  -1,  -3,  -7,  -7,  -4,  -2,  -3, -15,
        -3,  -4,  -8,  -5,  -4,  -7,  -4,  -4,  -4,  -5,  -4,  -5,  -4,  -3,  -4,  -4,  -4,  -5,  -2,  -3,  -4,  -4,  -9,  -7,  -4,  -4, -15,
        -1,  -6,  -7,  -7,  -5,  -9,  -5,  -3,  -7,  -7,  -6,  -6,  -7,  -5,  -4,   8,  -2,  -3,  -1,  -3,  -4,  -5, -12, -12,  -3,  -4, -15,
        -3,  -2, -12,  -2,   2, -11,  -6,   1,  -7,  -6,  -2,  -4,  -3,  -3,  -4,  -2,   8,  -1,  -4,  -5,  -4,  -6, -11, -10,   6,  -4, -15,
        -6,  -6,  -7,  -9,  -8,  -8,  -8,  -1,  -5,  -7,   1,  -8,  -3,  -5,  -5,  -3,  -1,   8,  -2,  -5,  -5,  -7,  -1,  -9,  -3,  -5, -15,
         0,  -1,  -2,  -3,  -4,  -6,  -1,  -5,  -6,  -7,  -3,  -7,  -5,   0,  -2,  -1,  -4,  -2,   6,   1,  -2,  -5,  -4,  -6,  -4,  -2, -15,
         0,  -2,  -7,  -4,  -5,  -8,  -5,  -6,  -2,  -4,  -2,  -6,  -3,  -1,  -3,  -3,  -5,  -5,   1,   7,  -3,  -2, -11,  -6,  -5,  -3, -15,
        -3,  -4,  -8,  -5,  -4,  -7,  -4,  -4,  -4,  -5,  -4,  -5,  -4,  -3,  -4,  -4,  -4,  -5,  -2,  -3,  -4,  -4,  -9,  -7,  -4,  -4, -15,
        -2,  -7,  -5,  -7,  -6,  -7,  -5,  -6,   2,   0,  -8,  -2,  -1,  -7,  -4,  -5,  -6,  -7,  -5,  -2,  -4,   7, -14,  -6,  -6,  -4, -15,
       -12,  -9, -14, -13, -15,  -4, -13,  -6, -12,  -9, -10,  -5, -11,  -7,  -9, -12, -11,  -1,  -4, -11,  -9, -14,  13,  -4, -13,  -9, -15,
        -7,  -6,  -3, -10,  -8,   2, -12,  -3,  -5,  -6,  -8,  -6, -10,  -4,  -7, -12, -10,  -9,  -6,  -6,  -7,  -6,  -4,  10,  -8,  -7, -15,
        -2,   1, -12,   2,   6, -12,  -4,   0,  -5,  -6,  -3,  -6,  -4,  -2,  -4,  -3,   6,  -3,  -4,  -5,  -4,  -6, -13,  -8,   6,  -4, -15,
        -3,  -4,  -8,  -5,  -4,  -7,  -4,  -4,  -4,  -5,  -4,  -5,  -4,  -3,  -4,  -4,  -4,  -5,  -2,  -3,  -4,  -4,  -9,  -7,  -4,  -4, -15,
       -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15, -15,   1
    ];

    static ref MAT: DMat<i32> = DMat::from_col_vec(27, 27, &*ARRAY);
}

#[inline]
fn lookup(a: u8) -> usize {
    if a == b'Y' {
        23 as usize
    } else if a == b'Z' {
        24 as usize
    } else if a == b'X' {
        25 as usize
    } else if a == b'*' {
        26 as usize
    } else {
        (a - 65) as usize
    }
}

pub fn pam40(a: u8, b: u8) -> i32 {
    let a = lookup(a);
    let b = lookup(b);

    MAT[(a, b)]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pam40() {
        let score1 = pam40(b'A', b'A');
        assert_eq!(score1, 6);
        let score2 = pam40(b'*', b'*');
        assert_eq!(score2, 1);
        let score3 = pam40(b'A', b'*');
        assert_eq!(score3, -15);
        let score4 = pam40(b'*', b'*');
        assert_eq!(score4, 1);
        let score5 = pam40(b'X', b'X');
        assert_eq!(score5, -4);
        let score6 = pam40(b'X', b'Z');
        assert_eq!(score6, -4);
    }
}
