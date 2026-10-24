package com.cleanops.repository;

import com.cleanops.model.User;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {

    boolean existsByFirebaseUid(String firebaseUid);

    boolean existsByEmail(String email);

    Optional<User> findByFirebaseUid(String firebaseUid);
}
