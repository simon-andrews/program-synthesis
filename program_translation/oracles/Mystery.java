class Mystery {
  public static void main(String[] args) {
    float x = Float.parseFloat(args[0]);
    float y = Float.parseFloat(args[1]);
    System.out.println(mystery(x, y));
  }

  static float mystery(float x, float y) {
    return x + y - 4;
  }
}

