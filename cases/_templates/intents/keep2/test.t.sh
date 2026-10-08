t_A1() { grep -qx 'Hello, World!' lib/greet.txt; }
t_A2() { [ "$(wc -l < lib/greet.txt | tr -d ' ')" = 1 ]; }
