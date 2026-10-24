package com.cleanops.controller;

import com.cleanops.model.User;
import com.cleanops.repository.UserRepository;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.Locale;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * User profile endpoints.
 *
 * <p>The caller is identified only by the Firebase UID that
 * {@code FirebaseAuthenticationFilter} puts in the security context after verifying the ID token.
 */
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    /** Strictly server-side: clients can never choose their own role. */
    private static final String DEFAULT_ROLE = "CITIZEN";

    private final UserRepository userRepository;

    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @PostMapping("/me")
    public ResponseEntity<?> createProfile(
            @AuthenticationPrincipal String firebaseUid,
            @Valid @RequestBody CreateProfileRequest body) {

        String email = body.email().trim().toLowerCase(Locale.ROOT);

        if (userRepository.existsByFirebaseUid(firebaseUid)) {
            return error(HttpStatus.CONFLICT, "Profile already exists for this account");
        }
        if (userRepository.existsByEmail(email)) {
            return error(HttpStatus.CONFLICT, "Email is already registered");
        }

        User user = new User();
        user.setFirebaseUid(firebaseUid);
        user.setName(body.name().trim());
        user.setEmail(email);
        user.setRole(DEFAULT_ROLE); // any "role" sent by the client is ignored

        try {
            User saved = userRepository.saveAndFlush(user);
            return ResponseEntity.status(HttpStatus.CREATED).body(UserResponse.from(saved));
        } catch (DataIntegrityViolationException race) {
            // Two concurrent requests passed the checks above; the UNIQUE constraints decide.
            return error(HttpStatus.CONFLICT, "Profile already exists for this account or email");
        }
    }

    @GetMapping("/me")
    public ResponseEntity<?> getMyProfile(@AuthenticationPrincipal String firebaseUid) {
        return userRepository.findByFirebaseUid(firebaseUid)
                .<ResponseEntity<?>>map(user -> ResponseEntity.ok(UserResponse.from(user)))
                .orElseGet(() -> error(HttpStatus.NOT_FOUND, "Profile not found. Call POST /api/v1/users/me first"));
    }

    // ----------------------------------------------------------------- errors

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .sorted()
                .collect(Collectors.joining("; "));
        return error(HttpStatus.BAD_REQUEST, message);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> handleUnreadableBody(HttpMessageNotReadableException ex) {
        return error(HttpStatus.BAD_REQUEST, "Request body is missing or is not valid JSON");
    }

    private static ResponseEntity<ApiError> error(HttpStatus status, String message) {
        return ResponseEntity.status(status)
                .body(new ApiError(status.value(), status.getReasonPhrase(), message));
    }

    // -------------------------------------------------------------------- DTOs

    /** Request body. Unknown properties (for example "role") are ignored by Jackson. */
    public record CreateProfileRequest(
            @NotBlank(message = "must not be blank")
            @Size(max = 255, message = "must be at most 255 characters")
            String name,

            @NotBlank(message = "must not be blank")
            @Email(message = "must be a valid email address")
            @Size(max = 255, message = "must be at most 255 characters")
            String email) {
    }

    /** Public view of a profile - the entity itself is never serialised. */
    public record UserResponse(UUID id, String firebaseUid, String name, String email, String role, Instant createdAt) {
        static UserResponse from(User u) {
            return new UserResponse(u.getId(), u.getFirebaseUid(), u.getName(), u.getEmail(), u.getRole(), u.getCreatedAt());
        }
    }

    /** Same shape as the 401 body written by FirebaseAuthenticationFilter. */
    public record ApiError(int status, String error, String message) {
    }
}
