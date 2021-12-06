(declare-const x Real)
(declare-const y Real)

(assert (= (+ x y 3) 15))
(assert (= (* x y) 20))
(assert (= (+ (/ y 2) x) 11))

(check-sat)
(get-model)