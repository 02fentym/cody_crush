# write below
public class Solution {
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in); // Create a Scanner object

        int number1 = input.nextInt(); // Read the first integer from user
        int number2 = input.nextInt(); // Read the second integer from user
        int sum = number1 + number2; // Calculate the sum

        System.out.println(sum); // Print the result
        input.close(); // Close the scanner
    }
}