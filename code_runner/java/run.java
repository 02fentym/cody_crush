import java.io.*;
import java.nio.file.*;
import java.util.*;

public class run {
    public static void main(String[] args) {
        File testDir = new File("tests");
        File studentFile = new File("student/Solution.java");

        List<Map<String, Object>> results = new ArrayList<>();

        if (!studentFile.exists()) {
            System.out.println("{\"error\": \"Missing Solution.java\"}");
            return;
        }

        try {
            Process compile = new ProcessBuilder("javac", "student/Solution.java")
                .redirectErrorStream(true)
                .start();
            compile.waitFor();
        } catch (Exception e) {
            System.out.println("{\"error\": \"Compilation failed\"}");
            return;
        }

        File[] inputs = testDir.listFiles((dir, name) -> name.endsWith(".in"));
        if (inputs == null) return;

        Arrays.sort(inputs, Comparator.comparing(File::getName));

        int passed = 0;

        for (File inFile : inputs) {
            String testName = inFile.getName().replace(".in", "");
            File outFile = new File(testDir, testName + ".out");

            try {
                String input = Files.readString(inFile.toPath());
                String expected = outFile.exists() ? Files.readString(outFile.toPath()).trim() : "";

                Process run = new ProcessBuilder("java", "-cp", "student", "Solution")
                    .redirectErrorStream(true)
                    .start();

                OutputStream stdin = run.getOutputStream();
                stdin.write(input.getBytes());
                stdin.flush();
                stdin.close();

                String actual = new String(run.getInputStream().readAllBytes()).trim();
                boolean pass = actual.equals(expected);

                if (pass) passed++;

                Map<String, Object> result = new HashMap<>();
                result.put("test", testName);
                result.put("passed", pass);
                result.put("expected", expected);
                result.put("actual", actual);
                results.add(result);

            } catch (Exception e) {
                Map<String, Object> result = new HashMap<>();
                result.put("test", inFile.getName());
                result.put("passed", false);
                result.put("expected", "");
                result.put("actual", "");
                result.put("error", e.getMessage());
                results.add(result);
            }
        }

        Map<String, Object> summary = new HashMap<>();
        summary.put("passed", passed);
        summary.put("total", results.size());
        summary.put("all_passed", passed == results.size());

        Map<String, Object> output = new HashMap<>();
        output.put("results", results);
        output.put("summary", summary);

        System.out.println(new com.google.gson.Gson().toJson(output));
    }
}
