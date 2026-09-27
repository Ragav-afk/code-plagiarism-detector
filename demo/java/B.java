public class B { // my own work
 static boolean check(int x){ if(x<=1) return false; for(int d=2;d*d<=x;d++){ if(x%d==0) return false; } return true; } }
