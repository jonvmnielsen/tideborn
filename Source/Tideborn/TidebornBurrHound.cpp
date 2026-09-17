#include "TidebornBurrHound.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornBurrHound::ATidebornBurrHound()
{
	CreatureRole = ETidebornCreatureRole::Threat;
	DisplayName = FName(TEXT("Burr-hound"));
	MaxHealth = 40.f;
	AggroRadius = 1000.f;
	AttackRange = 130.f;
	AttackDamage = 10.f;
	BodyColor = FLinearColor(0.55f, 0.2f, 0.15f);
	GetCharacterMovement()->MaxWalkSpeed = 460.f;

	// Low, wide body + short head cube (silhouette ≠ Kelp-back)
	GetCapsuleComponent()->InitCapsuleSize(55.f, 48.f);
	if (BodyMesh)
	{
		BodyMesh->SetRelativeScale3D(FVector(1.35f, 1.9f, 0.45f));
		BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -10.f));
	}

	HeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeadMesh"));
	HeadMesh->SetupAttachment(GetRootComponent());
	HeadMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HeadMesh->ComponentTags.Add(FName(TEXT("TidebornBody")));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		HeadMesh->SetStaticMesh(CubeMesh.Object);
		HeadMesh->SetRelativeScale3D(FVector(0.55f, 0.55f, 0.45f));
		HeadMesh->SetRelativeLocation(FVector(55.f, 0.f, 10.f));
	}
}
