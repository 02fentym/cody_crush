import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

public class run {

    // Extracts the public class name from a Java file
    private static String findPublicClassName(File javaFile) throws IOException {
        List<String> lines = Files.readAllLines(javaFile.toPath());
        for (String line : lines) {
            line = line.trim();
            if (line.startsWith("public class")) {
                String[] tokens = line.split("\\s+");
                if (tokens.length >= 3) {
                    return tokens[2].replace("{", "").trim();
                }
            }
        }
        throw new IOException("No public class found.");
    }

    public static void main(String[] args) {
        File testDir = new File("tests");
        File classDir = new File("classes");

        List<Map<String, Object>> results = new ArrayList<>();

        File studentFile = Arrays.stream(new File("student").listFiles())
            .filter(f -> f.getName().endsWith(".java"))
            .findFirst()
            .orElse(null);

        if (studentFile == null) {
            outputError("Missing Java file", results);
            return;
        }

        classDir.mkdirs();
        if (!studentFile.exists()) {
            outputError("Missing Solution.java", results);
            return;
        }

        String className;
        try {
            className = findPublicClassName(studentFile);
        } catch (IOException e) {
            outputError("Failed to determine public class: " + e.getMessage(), results);
            return;
        }


        // Check for missing imports
        try {
            String code = Files.readString(studentFile.toPath());
            List<String> imports = new ArrayList<>();
            if (code.contains("Scanner") || code.contains("ArrayList")) {
                imports.add("import java.util.*;");
            }
            // Add more checks for other packages if needed, e.g., java.io
            boolean hasImports = Arrays.stream(code.split("\n"))
                .anyMatch(line -> line.trim().startsWith("import"));

            if (!imports.isEmpty() && !hasImports) {
                Files.writeString(studentFile.toPath(), String.join("\n", imports) + "\n\n" + code);
            }

        } catch (IOException e) {
            outputError("Failed to process Solution.java: " + e.getMessage(), results);
            return;
        }

        // Compile Solution.java
        try {
            ProcessBuilder compilePb = new ProcessBuilder("javac", "-d", classDir.getPath(), studentFile.getPath());
            compilePb.redirectErrorStream(true);
            Process compile = compilePb.start();
            String compileOutput = new String(compile.getInputStream().readAllBytes()).trim();
            if (compile.waitFor() != 0) {
                outputError("Compilation failed: " + compileOutput.replace("\"", "\\\""), results);
                return;
            }
        } catch (Exception e) {
            outputError("Compilation error: " + e.getMessage().replace("\"", "\\\""), results);
            return;
        }

        // Detect package
        String packageName = "";
        try (BufferedReader br = new BufferedReader(new FileReader(studentFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith("package ")) {
                    packageName = line.replace("package ", "").replace(";", "").trim() + ".";
                    break;
                }
            }
        } catch (IOException e) {
            // No package
        }

        File[] inputs = testDir.listFiles((dir, name) -> name.endsWith(".in"));
        if (inputs == null || inputs.length == 0) {
            outputError("No test inputs", results);
            return;
        }

        Arrays.sort(inputs, Comparator.comparing(File::getName));
        int passed = 0;

        for (File inFile : inputs) {
            String testName = inFile.getName().replace(".in", "");
            File outFile = new File(testDir, testName + ".out");
            try {
                String input = Files.readString(inFile.toPath());
                String expected = outFile.exists() ? Files.readString(outFile.toPath()).trim() : "";

                ProcessBuilder runPb = new ProcessBuilder("java", "-cp", classDir.getPath(), packageName + className);
                Process run = runPb.start();

                OutputStream stdin = run.getOutputStream();
                stdin.write(input.getBytes());
                stdin.flush();
                stdin.close();

                String actual = new String(run.getInputStream().readAllBytes()).trim();
                String error = new String(run.getErrorStream().readAllBytes()).trim();
                boolean pass = actual.equals(expected);
                if (pass) passed++;

                Map<String, Object> result = new HashMap<>();
                result.put("test", testName);
                result.put("passed", pass);
                result.put("expected", expected);
                result.put("actual", actual);
                result.put("error", error);
                results.add(result);

                if (!run.waitFor(2, TimeUnit.SECONDS)) {
                    run.destroy();
                    throw new Exception("Timeout");
                }
            } catch (Exception e) {
                Map<String, Object> result = new HashMap<>();
                result.put("test", testName);
                result.put("passed", false);
                String expected;
                try {
                    expected = outFile.exists() ? Files.readString(outFile.toPath()).trim() : "";
                } catch (IOException ex) {
                    expected = "";
                }
                result.put("expected", expected);
                result.put("actual", "");
                result.put("error", e.getMessage());
                results.add(result);
            }
        }

        outputResults(results, passed);
    }

    private static void outputError(String error, List<Map<String, Object>> results) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("passed", 0);
        summary.put("total", results.size());
        summary.put("all_passed", false);

        Map<String, Object> output = new HashMap<>();
        output.put("results", results);
        output.put("summary", summary);
        output.put("error", error);

        System.out.println(new com.google.gson.Gson().toJson(output));
    }

    private static void outputResults(List<Map<String, Object>> results, int passed) {
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

